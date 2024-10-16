.PHONY: format
format:
	@echo "Formatting code..."
	find . -name '*.sh' -exec shfmt -w -i 4 '{}' +;

.PHONY: shellcheck
shellcheck:
	@echo "Running shellcheck..."
	find . -name '*.sh' -exec shellcheck --severity error '{}' +;

.PHONY: all
all: shellcheck format
	@echo "All checks passed!"
