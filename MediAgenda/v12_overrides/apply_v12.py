from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")

# Model
p = root / "app/src/main/java/com/mediagenda/app/model/Models.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '    var prescriptionCode: String = "",\n    var dispenseCode: String = "",',
    '    var prescriptionCode: String = "",\n    var prescriptionDate: String = "",\n    var dispenseCode: String = "",'
)
p.write_text(s, encoding="utf-8")

# JSON + CSV
p = root / "app/src/main/java/com/mediagenda/app/data/DataRepository.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '                prescriptionCode = o.optString("prescription_code"),\n                dispenseCode = o.optString("dispense_code"),',
    '                prescriptionCode = o.optString("prescription_code"),\n                prescriptionDate = o.optString("prescription_date"),\n                dispenseCode = o.optString("dispense_code"),'
)
s = s.replace(
    '                .put("prescription_code", m.prescriptionCode)\n                .put("dispense_code", m.dispenseCode)',
    '                .put("prescription_code", m.prescriptionCode)\n                .put("prescription_date", m.prescriptionDate)\n                .put("dispense_code", m.dispenseCode)'
)
s = s.replace(
    'N.º Prescrição;Código Acesso/Dispensa;Código Opção;Validade;Código Lido;Datas',
    'N.º Prescrição;Data Prescrição;Código Acesso/Dispensa;Código Opção;Validade;Código Lido;Datas'
)
s = s.replace(
    'm.prescriptionCode,m.dispenseCode,m.optionCode,m.validUntil,m.sourceBarcode,dates',
    'm.prescriptionCode,m.prescriptionDate,m.dispenseCode,m.optionCode,m.validUntil,m.sourceBarcode,dates'
)
p.write_text(s, encoding="utf-8")

# Gradle/version
p = root / "app/build.gradle.kts"
s = p.read_text(encoding="utf-8")
s = s.replace('versionCode = 2', 'versionCode = 3')
s = s.replace('versionName = "1.1.0"', 'versionName = "1.2.0"')
s = s.replace('com.google.android.gms:play-services-location:21.4.0',
              'com.google.android.gms:play-services-location:21.3.0')
if 'com.google.mlkit:barcode-scanning' not in s:
    s = s.replace(
        '    implementation("com.google.mlkit:text-recognition:16.0.1")\n',
        '    implementation("com.google.mlkit:text-recognition:16.0.1")\n'
        '    implementation("com.google.mlkit:barcode-scanning:17.3.0")\n'
    )
p.write_text(s, encoding="utf-8")

# MainActivity compile fixes from v1.1 + v1.2 prescription improvements
p = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")
s = s.replace('private val background = Color.parseColor("#F4F7F9")',
              'private val appBackground = Color.parseColor("#F4F7F9")')
s = s.replace('setBackgroundColor(background)', 'setBackgroundColor(appBackground)')
s = s.replace('private val text = Color.parseColor("#132238")',
              'private val mainTextColor = Color.parseColor("#132238")')
s = s.replace('setTextColor(text)', 'setTextColor(mainTextColor)')

if 'import com.google.mlkit.vision.barcode.BarcodeScanning' not in s:
    s = s.replace(
        'import com.google.mlkit.vision.common.InputImage\n',
        'import com.google.mlkit.vision.common.InputImage\n'
        'import com.google.mlkit.vision.barcode.BarcodeScanning\n'
    )

old = (
'    private fun recognizePrescription(uri: Uri) {\n'
'        val input = InputImage.fromFilePath(this, uri)\n'
'        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)\n'
'            .addOnSuccessListener { vision ->\n'
'                val med = PrescriptionOcrParser.parse(vision.text, pendingPrescriptionScan)\n'
'                pendingPrescriptionScan = ""\n'
'                editMedication(null, med, true)\n'
'            }\n'
'            .addOnFailureListener {\n'
'                showError("Não foi possível reconhecer a guia. Pode repetir a fotografia ou adicionar a medicação manualmente.")\n'
'            }\n'
'    }\n'
)
new = (
'    private fun recognizePrescription(uri: Uri) {\n'
'        val input = InputImage.fromFilePath(this, uri)\n'
'        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)\n'
'            .addOnSuccessListener { vision ->\n'
'                BarcodeScanning.getClient().process(input)\n'
'                    .addOnSuccessListener { barcodes ->\n'
'                        val photoCodes = barcodes.mapNotNull { it.rawValue }.filter { it.isNotBlank() }.joinToString("\\\\n")\n'
'                        val combinedCodes = listOf(pendingPrescriptionScan, photoCodes).filter { it.isNotBlank() }.joinToString("\\\\n")\n'
'                        val med = PrescriptionOcrParser.parse(vision.text, combinedCodes)\n'
'                        pendingPrescriptionScan = ""\n'
'                        editMedication(null, med, true)\n'
'                    }\n'
'                    .addOnFailureListener {\n'
'                        val med = PrescriptionOcrParser.parse(vision.text, pendingPrescriptionScan)\n'
'                        pendingPrescriptionScan = ""\n'
'                        editMedication(null, med, true)\n'
'                    }\n'
'            }\n'
'            .addOnFailureListener {\n'
'                showError("Não foi possível reconhecer a guia. Tente fotografar a folha inteira, direita e com boa luz.")\n'
'            }\n'
'    }\n'
)
if old not in s:
    raise SystemExit("recognizePrescription block not found")
s = s.replace(old, new, 1)

s = s.replace(
    '        val prescription = input("N.º da prescrição", m.prescriptionCode)\n'
    '        val dispense = input("Código de acesso e dispensa", m.dispenseCode)',
    '        val prescription = input("N.º da prescrição", m.prescriptionCode)\n'
    '        val prescriptionDate = input("Data da prescrição (YYYY-MM-DD)", m.prescriptionDate)\n'
    '        val dispense = input("Código de acesso e dispensa", m.dispenseCode)'
)
s = s.replace(
    'listOf(name,dose,indication,timeText,reminder,prescription,dispense,option,validUntil,dates)',
    'listOf(name,dose,indication,timeText,reminder,prescription,prescriptionDate,dispense,option,validUntil,dates)'
)
s = s.replace(
    'm.reminderTime=reminder.edit.text.toString().trim(); m.prescriptionCode=prescription.edit.text.toString().trim()\n'
    '                m.dispenseCode=dispense.edit.text.toString().trim();',
    'm.reminderTime=reminder.edit.text.toString().trim(); m.prescriptionCode=prescription.edit.text.toString().trim()\n'
    '                m.prescriptionDate=prescriptionDate.edit.text.toString().trim(); m.dispenseCode=dispense.edit.text.toString().trim();'
)
s = s.replace(
    'h.code.text=when{m.prescriptionCode.isNotBlank()->"Prescrição ${m.prescriptionCode}";m.dispenseCode.isNotBlank()->"Código de dispensa ${m.dispenseCode}";else->""}',
    'h.code.text=when{m.prescriptionCode.isNotBlank()->"Prescrição ${m.prescriptionCode}" + if(m.validUntil.isNotBlank()) "  •  válida até ${m.validUntil}" else "";m.dispenseCode.isNotBlank()->"Código de dispensa ${m.dispenseCode}";else->""}'
)

p.write_text(s, encoding="utf-8")
print("MediAgenda v1.2 patches applied")
