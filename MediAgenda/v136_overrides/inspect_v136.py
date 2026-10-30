from pathlib import Path
import re
base=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app')
main=(base/'MainActivity.kt').read_text(encoding='utf8')
print('MAIN LENGTH',len(main),'LINES',len(main.splitlines()))
for needle in ['private fun showProfileSelection(', 'private fun showProfileDialog(', 'private fun showMedicationDialog(', 'private fun showAppointmentDialog(', 'private fun showMedication', 'private fun showAppointment', 'Lar ou residência assistida', 'Contactos e responsável', 'Familiar / responsável pelo perfil','Contacto de referência','Cartão de Cidadão e identificação','Morada e unidade de saúde','NISS (11 dígitos)', 'val ownerOfAlarms','deviceButton.text="✎ FICHA"', 'cardContent.addView(row', 'showMedicationDialog(', 'showAppointmentDialog(']:
    i=main.find(needle)
    if i<0:
        print('NOT FOUND',needle);continue
    print('===',needle,'@',i,'===')
    before=800 if needle.startswith('private fun ') else 500
    after=6800 if needle in ['private fun showProfileSelection(', 'private fun showProfileDialog('] else 1900
    print(main[max(0,i-before):i+after])
for p in [base/'MedicationsActivity.kt',base/'MedicationActivity.kt',base/'AppointmentsActivity.kt',base/'AgendaActivity.kt']:
    if not p.exists():continue
    s=p.read_text(encoding='utf8')
    print('FILE',p.name,len(s))
    for m in re.finditer('MaterialAlertDialogBuilder|setTitle\\(|\\.show\\(\\)|Dialog\\(',s):
        j=m.start()
        if any(x in s[max(0,j-450):j+300].lower() for x in ['medica','agend','consult','dose','marca']):
            print('DIALOG',p.name,j,s[max(0,j-350):j+500])
