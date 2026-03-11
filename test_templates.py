"""Test report templates."""
from reporter import ReportGenerator, REPORT_TEMPLATES

print("Available templates:")
for k, v in REPORT_TEMPLATES.items():
    print(f"  {k}: {v['description']}")

print("\nTesting template instantiation:")
for template_name in REPORT_TEMPLATES.keys():
    try:
        gen = ReportGenerator(template=template_name)
        print(f"  [OK] {template_name}: OK")
    except Exception as e:
        print(f"  [ERROR] {template_name}: {e}")
