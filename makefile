
.PHONY: pre-commit
pre-commit:
	pre-commit run -a

.PHONY: pre-commit-update
pre-commit-update:
	pre-commit autoupdate
