#!/bin/bash
# Run linting and formatting checks

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running Ruff (Format & Lint)...${NC}"
# Run formatter first
ruff format .
# Run linter with autofix
ruff check . --fix

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Ruff checks passed!${NC}"
else
    echo -e "${RED}Ruff found issues.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Running Mypy (Type Check)...${NC}"
mypy .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Mypy checks passed!${NC}"
else
    echo -e "${RED}Mypy found type errors.${NC}"
    exit 1
fi

echo -e "\n${GREEN}All quality checks passed!${NC}"
