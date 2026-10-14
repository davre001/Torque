"""Shared managed test configuration; no web-server dependency."""
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SetupConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    framework: Literal['npm', 'pytest']
    test_files: list[str] = Field(min_length=1, max_length=10)
    editable_files: list[str] = Field(min_length=1, max_length=10)

    @field_validator('test_files', 'editable_files')
    @classmethod
    def paths(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('File paths must be unique')
        for path in value:
            if not re.fullmatch(r'[A-Za-z0-9_./-]{1,180}', path):
                raise ValueError('Use explicit repository-relative file paths')
            if any(part in {'', '.', '..'} or part.startswith('.') for part in path.split('/')):
                raise ValueError('Hidden files, absolute paths and parent paths are unsupported')
            if any(part in {'node_modules', 'venv', '__pycache__'} for part in path.split('/')):
                raise ValueError('Dependency directories are unsupported')
        return value

    @model_validator(mode='after')
    def independent(self):
        if set(self.test_files) & set(self.editable_files):
            raise ValueError('Test files cannot also be editable files')
        if any(p.rsplit('/', 1)[-1] in {'package.json', 'package-lock.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'conftest.py', 'pytest.ini', 'pyproject.toml', 'requirements.txt'} for p in self.editable_files):
            raise ValueError('Dependency and test configuration cannot be edited by the agent')
        for path in self.editable_files:
            name = path.rsplit('/', 1)[-1]
            if any(part.lower() in {'test', 'tests', '__tests__'} for part in path.split('/')) or re.search(r'\.(test|spec)\.', name) or name.startswith(('test_', 'vitest.config.', 'jest.config.', 'vite.config.', 'tsconfig')) or name.endswith('_test.py'):
                raise ValueError('Test files and test configuration cannot be edited by the agent')
        if self.framework == 'npm':
            manifests = [p for p in self.test_files if p.rsplit('/', 1)[-1] == 'package.json']
            if not manifests or not ('pnpm-lock.yaml' in self.test_files or any(p[:-12]+'package-lock.json' in self.test_files for p in manifests)):
                raise ValueError('Include package manifests and an npm or pnpm lockfile in the frozen tests')
        if self.framework == 'pytest' and not any(p.endswith('.py') and p.rsplit('/', 1)[-1] != 'conftest.py' for p in self.test_files):
            raise ValueError('Include at least one Python test file')
        return self

