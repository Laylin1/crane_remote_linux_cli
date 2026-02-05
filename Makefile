.PHONY: install uninstall docker-build docker-up docker-down help

INSTALL_PATH ?= /usr/local/bin

install:
	@sudo cp crane_scr $(INSTALL_PATH)/crane && sudo chmod +x $(INSTALL_PATH)/crane
	@echo "✓ crane installed to $(INSTALL_PATH)/crane"

uninstall:
	@sudo rm -f $(INSTALL_PATH)/crane
	@echo " crane removed"

docker-build:
	@docker-compose build

docker-up:
	@docker-compose up -d

docker-down:
	@docker-compose down

docker-logs:
	@docker-compose logs -f

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  install       - Install crane command"
	@echo "  uninstall     - Remove crane command"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-up     - Start containers"
	@echo "  docker-down   - Stop containers"
	@echo "  docker-logs   - View logs"