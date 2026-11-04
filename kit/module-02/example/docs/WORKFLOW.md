# Workflow
```mermaid
flowchart TD
  A[User types a name] --> B[App calls the API]
  B --> C{Rows returned?}
  C -- yes --> D[Show table]
  C -- no --> E[Show message]
```
