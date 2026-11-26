# Spec: Archive a project instead of deleting it

**Status:** Approved · **Decider:** Dana Okafor (projects team) · **Links:** PROJ-412, SUP-88

<!-- Golden example. The product, people, paths and numbers are invented. -->

## Why

The project list shows every project of an account and has no filter. Owners delete finished projects to shorten the list. Deleting a project also removes its tasks. Support restored 41 deleted projects from backups in October.

After this change, an owner can archive a project. An archived project leaves the default list and rejects write requests. Archiving preserves the project and its tasks. This spec covers the API only.

## Example

Ana archives her project at 10:15 UTC on 4 March 2026:

```http
POST /v1/projects/prj_301/archive
Authorization: Bearer sk_test_ana
```

```http
HTTP/1.1 200 OK

{"id": "prj_301", "name": "Website 2023", "created_at": "2023-01-09T08:00:00Z", "archived_at": "2026-03-04T10:15:00Z"}
```

## Check

1. Archive a project as its owner with `curl`, in the local environment.
2. Send `GET /v1/projects`. The list does not have the project.
3. Send `GET /v1/projects?include_archived=true`. The list has the project.
4. Send a `PATCH` request to the project. The response is 409.

## Requirements

| ID | Requirement |
|---|---|
| R1 | When an owner sends an archive request for a project that is not archived, the API MUST set `archived_at` to the current time and return 200 with the project. |
| R2 | When an owner sends an archive request for an archived project, the API MUST return 200 with the project and keep the value of `archived_at`. |
| R3 | When an owner sends an unarchive request, the API MUST set `archived_at` to null and return 200 with the project. |
| R4 | When a member who is not an owner sends an archive request or an unarchive request, the API MUST return 403 `not_project_owner` and keep the value of `archived_at`. |
| R5 | When a member sends a write request to an archived project, the API MUST reject the request with 409 `project_archived`. |
| R6 | When the `include_archived` parameter of a request to `GET /v1/projects` is absent or has a value other than `true`, the API MUST omit each archived project from the list. |
| R7 | When a request to `GET /v1/projects` has the parameter `include_archived=true`, the API MUST list each archived project in the same way as a project that is not archived. |
| R8 | The API MUST include `archived_at` in each project that it returns. |

## Design

- **Migration.** The migration adds one nullable column, `archived_at TIMESTAMPTZ`, to the table `projects`. The migration changes no rows.
- **Check order.** The API checks authentication, then membership, as today. For an archive request or an unarchive request, the API then checks the owner role. For a write request, the API then checks for an archived project, before every remaining check.
- **Two archive requests at the same time.** The archive request sets `archived_at` with one update that has the condition `archived_at IS NULL`. Both responses return the value that the first update set.
- **A write request during an archive request.** The write request either commits before the archive request commits or returns 409 `project_archived`.
- **List.** The list endpoint applies R6 in the database query, before pagination.
- **Responses.** The archive request and the unarchive request return the project in the same shape as `GET /v1/projects/{id}`. The value of `archived_at` has the same format as `created_at`.
- **Request bodies.** The API ignores the body of an archive request and of an unarchive request. In every other request body, the API treats `archived_at` as it treats the read-only field `created_at` today.
- **Error codes.** The error codes `not_project_owner` and `project_archived` are new and use the existing error body shape. The owner-role check of each existing endpoint keeps its current error code.

## Cases

The setup for every case:

- Ana is the owner of `prj_301` and of `prj_302`.
- Ben is a member of both and is not an owner of either.
- Cy is a member of neither.
- `prj_301` has one task, `tsk_9`. `prj_302` is not archived.
- All times are UTC on 4 March 2026.

### Archive and unarchive

| Given | When | Then | Covers |
|---|---|---|---|
| `prj_301` is not archived | Ana sends an archive request for `prj_301` at 10:15 | 200. `archived_at` is `2026-03-04T10:15:00Z`. | R1, R8 |
| Ana archived `prj_301` at 10:15 | Ana sends an archive request for `prj_301` at 10:20 | 200. `archived_at` is `2026-03-04T10:15:00Z`. | R2 |
| Ana archived `prj_301` | Ana sends an unarchive request for `prj_301` | 200. `archived_at` is null. | R3 |
| `prj_301` is not archived | Ana sends an unarchive request for `prj_301` | 200. `archived_at` is null. | R3 |
| `prj_301` is not archived | Ana sends `GET /v1/projects/prj_301` | 200. `archived_at` is null. | R8 |

### Who can archive

| Given | When | Then | Covers |
|---|---|---|---|
| `prj_301` is not archived | Ben sends an archive request for `prj_301` | 403 `not_project_owner`. `prj_301` is not archived. | R4 |
| Ana archived `prj_301` | Ben sends an unarchive request for `prj_301` | 403 `not_project_owner`. `prj_301` stays archived. | R4 |
| `prj_301` is not archived | Cy sends an archive request for `prj_301` | 404, as for every other request from Cy to `prj_301`. `prj_301` is not archived. | Unchanged |

### Requests to an archived project

| Given | When | Then | Covers |
|---|---|---|---|
| Ana archived `prj_301`, which has the name `Website 2023` | Ana sends `PATCH /v1/projects/prj_301` with the name `Website 2026` | 409 `project_archived`. The name is `Website 2023`. | R5 |
| Ana archived `prj_301` | Ben sends `POST /v1/projects/prj_301/tasks` | 409 `project_archived`. `prj_301` has one task. | R5 |
| Ana archived `prj_301` | Ana sends `DELETE /v1/projects/prj_301` | 409 `project_archived`. `prj_301` exists. | R5 |
| Ana archived `prj_301` | Ben sends `GET /v1/projects/prj_301/tasks` | 200 and `tsk_9`. | Unchanged |

### The project list

| Given | When | Then | Covers |
|---|---|---|---|
| Ana archived `prj_301` | Ana sends `GET /v1/projects` | The list has `prj_302` and does not have `prj_301`. | R6 |
| Ana archived `prj_301` | Ana sends `GET /v1/projects?include_archived=false` | The list has `prj_302` and does not have `prj_301`. | R6 |
| Ana archived `prj_301` | Ana sends `GET /v1/projects?include_archived=true` | The list has `prj_301` and `prj_302`. | R7 |
