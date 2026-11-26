# Glossary

One term has one meaning. Use the term in the first column. The linter rejects each word in the last column.

This glossary belongs to the invented project in `golden-example.md`. Replace the rows with the terms of your project.

| Term | Meaning | Do not use |
|---|---|---|
| API | The projects HTTP application that the spec changes. | server, backend, service |
| member | A user who has a role on the project. | collaborator, participant |
| owner | A member who has the role `owner` on the project. | admin, manager |
| archived project | A project whose `archived_at` is not null. | hidden project, inactive project, closed project |
| archive request | `POST /v1/projects/{id}/archive`. | |
| unarchive request | `POST /v1/projects/{id}/unarchive`. | restore request |
| write request | A `PATCH` or `DELETE` request to `/v1/projects/{id}`, or a `POST`, `PATCH` or `DELETE` request to `/v1/projects/{id}/tasks` or to a path under `/v1/projects/{id}/tasks`. | mutation, update request |
