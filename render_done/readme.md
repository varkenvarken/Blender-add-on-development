# render_done Package

When creating a rather complicated import graph it is import to check if there are no cyclic dependencies. In this case there are none, see the graph below.

Note: The graph was created by Github copilot but verified by me. The prompt was:

    create a mermaid diagram that shows the import dependancies,
    but only for the modules defined in the render_done package

## Import Dependencies

```mermaid
graph TD
    utils["utils.py"]
    mail["mail.py"]
    handlers["handlers.py"]
    operators["operators.py"]
    preferences["preferences.py"]
    init["__init__.py"]
    
    mail -->|imports get_package_name| utils
    handlers -->|imports read_password, send_smtp_message| utils
    handlers -->|imports send_smtp_message| mail
    operators -->|imports get_package_name, read_password| utils
    operators -->|imports verify_smtp_connection| mail
    preferences -->|imports get_package_name, read_password| utils
    preferences -->|imports is_valid_email_address| mail
    preferences -->|imports ReadPasswordFromFile, VerifyServer| operators
    init -->|imports all| handlers
    init -->|imports all| mail
    init -->|imports all| utils
    init -->|imports all| preferences
    init -->|imports all| operators
    
    style utils fill:#e1f5ff
    style mail fill:#fff3e0
    style handlers fill:#f3e5f5
    style operators fill:#e8f5e9
    style preferences fill:#fce4ec
    style init fill:#fff9c4
```

## Module Overview

- **utils.py** - Utility functions with no internal dependencies (get_package_name, read_password)
- **mail.py** - Email handling and SMTP operations (depends on utils)
- **handlers.py** - Render event handlers (depends on utils and mail)
- **operators.py** - Blender operators (depends on utils and mail)
- **preferences.py** - Addon preferences UI (depends on utils, mail, and operators)
- **__init__.py** - Main module initialization (imports and registers all others)
