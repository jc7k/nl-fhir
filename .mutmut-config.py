# Mutmut Configuration for NL-FHIR
# Mutation testing finds weaknesses in test suites

def pre_mutation(context):
    """
    Called before each mutation is run.
    Can be used to skip certain mutations or files.
    """
    # Skip test files themselves
    if 'test_' in context.filename:
        context.skip = True
    
    # Skip __pycache__ and .venv
    if '__pycache__' in context.filename or '.venv' in context.filename:
        context.skip = True
    
    # Skip generated files
    if context.filename.endswith(('.pyc', '.pyo')):
        context.skip = True


def post_mutation(context):
    """
    Called after each mutation is tested.
    Can be used for custom reporting or cleanup.
    """
    pass
