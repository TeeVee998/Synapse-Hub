#!/usr/bin/env bats

@test 'verify CLI returns version' {
  run python3 tools/cli.py --version
  [ "$status" -eq 0 ]
}
