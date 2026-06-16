// semantic-release config (CommonJS so the release-notes template can be read
// from an external .hbs file at load time).
//
// Why a custom releaseNotes.template:
//   semantic-release-gitmoji's bundled default template only renders 5 gitmoji
//   groups (:boom: / :sparkles: / :bug: / :ambulance: / :lock:). Our maintenance
//   releases are driven by other gitmoji (:wrench:, :recycle:, :arrow_up:, ...),
//   so the default template produced EMPTY release notes for those (e.g. v1.12.1,
//   v1.10.2). The template in .github/release-notes-template.hbs adds a section
//   for every gitmoji listed in releaseRules below, so patch/maintenance releases
//   get meaningful notes.
//
// get-config.js deep-merges (lodash mergeWith) the plugin options over the
// plugin's defaults, so supplying only releaseNotes.template keeps the default
// commitTemplate partial and the non-semver (semver:false) grouping behaviour.

const fs = require("fs");
const path = require("path");

const releaseNotesTemplate = fs.readFileSync(
  path.join(__dirname, ".github", "release-notes-template.hbs"),
  "utf8",
);

module.exports = {
  branches: ["main"],
  tagFormat: "v${version}",
  plugins: [
    [
      "semantic-release-gitmoji",
      {
        releaseRules: {
          major: [":boom:"],
          minor: [":sparkles:"],
          patch: [
            ":bug:",
            ":ambulance:",
            ":lock:",
            ":zap:",
            ":rocket:",
            ":wrench:",
            ":recycle:",
            ":fire:",
            ":arrow_up:",
            ":arrow_down:",
            ":pushpin:",
            ":pencil2:",
            ":globe_with_meridians:",
            ":alien:",
            ":card_file_box:",
          ],
        },
        releaseNotes: {
          template: releaseNotesTemplate,
        },
      },
    ],
    [
      "@semantic-release/exec",
      {
        prepareCmd:
          "uv version --no-sync ${nextRelease.version} && bash .github/scripts/sync-version-refs.sh ${nextRelease.version} && uv lock",
      },
    ],
    [
      "@semantic-release/changelog",
      {
        changelogFile: "CHANGELOG.md",
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: [
          "pyproject.toml",
          "uv.lock",
          "CHANGELOG.md",
          "README.md",
          "docs/**/*.md",
          ".github/workflows/*.yml",
        ],
        message:
          ":bookmark: chore(release): v${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
      },
    ],
    "@semantic-release/github",
  ],
};
