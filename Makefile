.PHONY: format
format:
	@echo "Formatting code..."
	find . -name '*.sh' -exec shfmt -w -i 4 '{}' +;

.PHONY: shellcheck
shellcheck:
	@echo "Running shellcheck..."
	find . -name '*.sh' -exec shellcheck --severity error '{}' +;

.PHONY: pre-commit
pre-commit:
	@echo "Running pre-commit..."
	pre-commit run --all-files

.PHONY: all
all: shellcheck format
	@echo "All checks passed!"

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  format: Run shfmt to format shell scripts"
	@echo "  shellcheck: Run shellcheck to lint shell scripts"
	@echo "  pre-commit: Run pre-commit checks"
	@echo "  all: Run all checks"
	@echo "  help: Show this help message"
