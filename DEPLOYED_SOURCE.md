# Deployed source reconciliation

On 27 October 2026 this fork was reconciled with the package imported by the
live Dominion Maya 2024 session:

`D:/dev/dominion_trunk/tools/TechArt/pipeline_dcc/src/vendor/python/pyblish_qml`

The Git working copy is separate:
`F:/dev/jagex_github/pyblish-qml`. Editing or pushing this repository does not
update Maya's vendored package. SoA has its own deployed copy and was not used
as the source of truth for this reconciliation.

The synchronized package includes structured validation feedback and legacy
error fallback, report export, scene invalidation, instance browsing and
host-confirmed publish selection, plus the existing tag settings UI/transport.
Maya-specific scene guards and publish settings call the deployed JAM host
modules; this fork is not a standalone replacement for those modules.

The runtime version remains 1.16.5 to preserve exact deployed source parity.
This synchronization commit does not create a new release tag or publish a
wheel; the historical v1.16.5 tag still identifies the earlier release.
Use the Git commit to identify this source snapshot until a release is prepared.

## Update: release 1.16.6

Version 1.16.6 is the first release after the reconciliation above. The Maya scene guard and publish
settings no longer import the host pipeline: the service calls whatever is registered through
`pyblish_qml.hooks` (see its docstring) and does nothing for what is not. A pipeline that provided those
modules directly now registers them as providers. The scene snapshot's context key is `hooks.SCENE_KEY`.
The wording above about calling the deployed host modules describes the earlier snapshot.
