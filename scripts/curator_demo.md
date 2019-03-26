# Curator Demo

Generated Script:

```python
# Import the KiProject class:
from kitools import KiProject

# Open the KiProject:
kiproject = KiProject("/tmp/demo_curator_e6a4296c")

# Add some new files and push them:
kiproject.data_add("data/core/new_study_file_test_file_1_aee15bc4.dat")
kiproject.data_add("data/discovered/new_study_file_test_file_1_c24439d2.dat")
kiproject.data_add("data/derived/new_study_file_test_file_1_1f4e9c02.dat")
kiproject.data_push()

# Push some changed files:
kiproject.data_push("core_test_file_1_0e3e249c.dat")
kiproject.data_push("core_test_file_1_3ae4fc71.dat")
kiproject.data_push("core_test_file_1_4d06c1b4.dat")
```
