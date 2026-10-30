#!/bin/sh
# Execute headless Katalon suite with automatic process cleanup
katalonc -noSplash -runMode=console -projectPath="$1" -testSuitePath="Test Suites/SmokeSuite" -browserType="Chrome (headless)"
