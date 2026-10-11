# Independent kokon acceptance suite

The vendored seccomp_profile.json is from Microsoft Playwright v1.63.0,
utils/docker/seccomp_profile.json (Apache-2.0). It permits Chromium's user-namespace
sandbox while retaining syscall filtering. The remote VM uses Ubuntu 22.04 to avoid
Ubuntu 24.04 host user-namespace restrictions. Chromium sandboxing remains enabled;
containers still run without network or capabilities and with read-only mounts.

These browser tests check all three issue criteria against the pinned source mounted
at /workspace. The agent cannot edit the suite, which is mounted read-only at /acceptance.
They emit a machine-readable result so an infrastructure failure cannot be mistaken
for reproduction of the issue.

Docker is currently unavailable in the development workspace. The image and suite
are prepared but have not been executed. Browser sandbox support must work inside the
reviewed runner; launch failure is an infrastructure failure, never a passing result.
Do not disable the browser sandbox to force a demo.

Build on a machine running Linux containers:

```powershell
docker build -t torque-kokon-tests tests/acceptance/kokon
docker image inspect torque-kokon-tests --format '{{.Id}}'
```

Use the immutable sha256 image ID printed by inspect as the recipe's image value.
An existing named image with a RepoDigest is also supported.
Set suite_directory to the absolute path to this folder. The command is
`["python", "/acceptance/test_reduced_motion.py"]`.

The build accesses package registries; the actual test execution has no external network
and receives no provider/GitHub keys. Compatibility with resource limits and Chromium's
sandbox remains a live-run acceptance check.
