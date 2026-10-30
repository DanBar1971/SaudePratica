from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
ui=base/"HealthExpensesActivity.kt"
s=ui.read_text(encoding="utf-8")
assert 'val background=ContextCompat.getDrawable(this,R.drawable.saude_background)' in s
s=s.replace('val background=ContextCompat.getDrawable(this,R.drawable.saude_background)',
            'val artwork=ContextCompat.getDrawable(this,R.drawable.saude_background)',1)
s=s.replace('if(background is BitmapDrawable)background.gravity=Gravity.FILL',
            'if(artwork is BitmapDrawable)artwork.gravity=Gravity.FILL',1)
s=s.replace('background=if(dark&&background!=null)',
            'background=if(dark&&artwork!=null)',1)
s=s.replace('LayerDrawable(arrayOf(background,ColorDrawable(',
            'LayerDrawable(arrayOf(artwork,ColorDrawable(',1)
assert 'private fun current():List<HealthExpense>=vault.list().filter{' in s
s=s.replace('private fun current():List<HealthExpense>=vault.list().filter{',
            'private fun current():List<HealthExpense> = vault.list().filter{',1)
ui.write_text(s,encoding="utf-8")

backup=base/"data/FamilyBackupStore.kt"
s=backup.read_text(encoding="utf-8")
old='''    private fun File.safe():Boolean=canonicalPath==absolutePath'''
new='''    // /data/user/0 may itself be an Android OS symlink. Check the file
    // against the canonical root rather than the raw absolute path.
    private fun File.safe():Boolean =
        !java.nio.file.Files.isSymbolicLink(toPath()) &&
        (canonicalFile==root.canonicalFile ||
         canonicalPath.startsWith(root.canonicalPath+"/"))'''
assert s.count(old)==1
backup.write_text(s.replace(old,new,1),encoding="utf-8")
print("Fixed Kotlin expense UI and full-backup path check on Android device symlink directories.")
