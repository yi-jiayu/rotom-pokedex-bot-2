def pytest_assertrepr_compare(config, op, left, right):
    if op in ('==', '!='):
        return [f'{left} {op} {right}']
