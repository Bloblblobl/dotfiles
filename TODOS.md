# TODOs

## High priority

- [ ] Add interactive reconciliation for existing home files, including Ubuntu's
  default `~/.bashrc`, without silently overwriting files.
- [ ] Test Windows setup natively; detect installed winget packages and WSL,
  and verify reboot/resume behavior.
- [ ] Implement and test macOS setup, dependencies, shell defaults, and tmux
  clipboard handling.
- [ ] Test GitHub login, secure storage and plaintext fallback, reruns, opt-out,
  and isolation from tracked Git configuration.

## Next

- [ ] Install tmux and Starship where supported; initialize Starship in shells.
- [ ] Unify platform entry points and simplify the Windows-to-WSL handoff;
  avoid assuming `curl` is installed.
- [ ] Add CI coverage for PowerShell, path conflicts, authentication/package
  mocks, and disposable first-run installs.
- [ ] Validate Python/GitHub CLI versions; handle missing dependencies and
  interrupted clones.

## Later

- [ ] Add `.gitattributes` rules to prevent CRLF-only diffs.
- [ ] Document/test Nerd Font requirements and non-WSL clipboard integrations.
- [ ] Evaluate pinned releases instead of downloading bootstrap from `master`.
