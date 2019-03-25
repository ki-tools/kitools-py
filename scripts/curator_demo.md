# Curator Demo

Generate Script:

```python
# Import the KiProject class:
from kitools import KiProject

# Open the KiProject:
kiproject = KiProject("/tmp/demo_curator_3c38346f")

# Add some new files and push them:
kiproject.data_add("/tmp/demo_curator_3c38346f/data/core/new_study_file_test_file_1_2a4ff9f4.dat")
kiproject.data_add("/tmp/demo_curator_3c38346f/data/discovered/new_study_file_test_file_1_c515ee93.dat")
kiproject.data_add("/tmp/demo_curator_3c38346f/data/derived/new_study_file_test_file_1_365652f9.dat")
kiproject.data_push()

# Push some changed files:
kiproject.data_push("core_test_file_1_158cd1d1.dat")
kiproject.data_push("core_test_file_1_e22da4ac.dat")
kiproject.data_push("core_test_file_1_e5cfe8b9.dat")

```
