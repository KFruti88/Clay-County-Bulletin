## ⚙️ 5. GitHub Priority: Compatibility & Caching
> **MANDATORY:** These rules override all other styling or logic requests.

- **Universal Rendering:** - Master container MUST be `width: 90%; margin: auto;`.
    - Height MUST be `height: auto;` to scale with the dynamic row count of the Google Sheet.
    - Use `display: grid;` with `auto-fit` to ensure cards never overlap or run off-screen on any device (iPhone to 4K TV).
  
- **Priority Caching (Cache Busting):**
    - Every `<link>` for CSS and every `<script>` tag MUST include a version query string.
    - Format: `filename.extension?v=[TIMESTAMP_OR_VERSION]` (e.g., `style.css?v=1.24`).
    - **Reason:** This ensures GitHub Pages reflects real-time changes without requiring a manual cache clear.

- **Cross-Browser Standards:**
    - Use `-webkit-` prefixes for Safari/iOS compatibility.
    - No fixed pixel heights on cards; use `min-height` or `flex-grow` to allow content to breathe.
