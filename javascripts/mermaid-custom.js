document.addEventListener('DOMContentLoaded', function () {
  initializeMermaid();
});

// Initialize Mermaid on page show (initial load and back navigation)
window.onpageshow = function (event) {
  if (event.persisted) {
    console.log('Page restored from bfcache, reinitializing Mermaid');
    initializeMermaid();
  }
};

// Mermaid initialization function
function initializeMermaid() {
  const isDarkMode =
    window.matchMedia('(prefers-color-scheme: dark)').matches ||
    document.documentElement.getAttribute('data-md-color-scheme') === 'slate';

  // Clear existing Mermaid instances
  if (window.mermaid) {
    window.mermaid.reset(); // Reset Mermaid state
    console.log('Mermaid instance reset');
  }

  mermaid.initialize({
    startOnLoad: true,
    theme: isDarkMode ? 'dark' : 'default',
    themeCSS: `
                        .node rect, .node polygon {
                                stroke-width: 1px !important;
                        }
                        .cluster rect {
                                fill: ${
                                  isDarkMode ? '#1e1e1e' : '#f5f5f5'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#444' : '#666'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .label {
                                font-family: "trebuchet ms", verdana, arial, sans-serif !important;
                                font-size: 18px !important;
                                color: ${
                                  isDarkMode ? '#fff' : '#333'
                                } !important;
                        }
                        .edgeLabel {
                                background-color: ${
                                  isDarkMode
                                    ? 'rgba(255, 255, 255, 0.1)'
                                    : 'rgba(0, 0, 0, 0.1)'
                                } !important;
                                color: ${
                                  isDarkMode ? '#fff' : '#333'
                                } !important;
                                padding: 3px 6px !important;
                                border-radius: 3px !important;
                        }
                        .edgePath .path {
                                stroke: ${
                                  isDarkMode ? '#ccc' : '#666'
                                } !important;
                                stroke-width: 2.5px !important;
                        }
                        .arrowheadPath {
                                fill: ${
                                  isDarkMode ? '#ccc' : '#666'
                                } !important;
                        }
                        .input {
                                fill: ${
                                  isDarkMode ? '#ffca28' : '#ffca28'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#fb8c00' : '#fb8c00'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .process {
                                fill: ${
                                  isDarkMode ? '#43a047' : '#43a047'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#2e7d32' : '#2e7d32'
                                } !important;
                                stroke-width: 2px !important;
                        }
                        .output {
                                fill: ${
                                  isDarkMode ? '#42a5f5' : '#42a5f5'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#1976d2' : '#1976d2'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .api {
                                fill: ${
                                  isDarkMode ? '#e91e63' : '#e91e63'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#c2185b' : '#c2185b'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .external {
                                fill: ${
                                  isDarkMode ? '#78909c' : '#78909c'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#546e7a' : '#546e7a'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .start {
                                fill: ${
                                  isDarkMode ? '#9c27b0' : '#9c27b0'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#6a1b9a' : '#6a1b9a'
                                } !important;
                                stroke-width: 2px !important;
                        }
                        .condition {
                                fill: ${
                                  isDarkMode ? '#e91e63' : '#e91e63'
                                } !important;
                                stroke: ${
                                  isDarkMode ? '#c2185b' : '#c2185b'
                                } !important;
                                stroke-width: 1px !important;
                        }
                        .mermaid {
                                transform: scale(1.2) !important;
                                transform-origin: top left !important;
                        }
                `,
  });

  mermaid.run();
  console.log('Mermaid initialized and run');

  // Monitor for diagram additions with MutationObserver
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        const mermaidElements = document.querySelectorAll('.mermaid');
        if (mermaidElements.length) {
          mermaid.run();
          console.log('Mermaid re-run due to DOM mutation');
        }
      }
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

// Event listener for color scheme changes
window
  .matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', function (e) {
    const newIsDarkMode =
      e.matches ||
      document.documentElement.getAttribute('data-md-color-scheme') === 'slate';
    initializeMermaid();
    console.log('Theme changed, Mermaid reinitialized');
  });
