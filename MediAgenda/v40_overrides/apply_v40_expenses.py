from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
for name,dest in (
    ("HealthExpensesStore.kt",base/"expenses/HealthExpensesStore.kt"),
    ("HealthExpensesActivity.kt",base/"HealthExpensesActivity.kt"),
):
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(Path("MediAgenda/v40_overrides",name)
        .read_text(encoding="utf-8"),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
anchor='''        <activity android:name=".WorkMedicineActivity" android:exported="false" />'''
assert s.count(anchor)==1,"Missing work activity anchor"
s=s.replace(anchor,anchor+'''
        <activity android:name=".HealthExpensesActivity" android:exported="false" />''',1)
manifest.write_text(s,encoding="utf-8")

paths=root/"app/src/main/res/xml/saudepratica_document_paths.xml"
s=paths.read_text(encoding="utf-8")
assert s.count("</paths>")==1
s=s.replace("</paths>",'''    <files-path name="health_expenses"
        path="saudepratica_expenses/" />
    <cache-path name="health_expenses_camera"
        path="saudepratica_expense_camera/" />
</paths>''',1)
paths.write_text(s,encoding="utf-8")

main=base/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
anchor='''            DashboardModule("🏥", "Saúde Ocupacional", "Medicina do Trabalho e exames") {
                startActivity(Intent(this,WorkMedicineActivity::class.java)
                    .putExtra(WorkMedicineActivity.EXTRA_PROFILE_ID,activeProfileId))
            },'''
assert s.count(anchor)==1,"Missing occupational health dashboard button"
s=s.replace(anchor,anchor+'''
            DashboardModule("🧾", "Despesas de Saúde", "Faturas, receitas e IRS") {
                startActivity(Intent(this,HealthExpensesActivity::class.java)
                    .putExtra(HealthExpensesActivity.EXTRA_PROFILE_ID,activeProfileId))
            },''',1)
main.write_text(s,encoding="utf-8")

print("SaúdePrática v1.9.21 adds per-user expenses module with invoices, receipts, reimbursement and e-Fatura verification.")
