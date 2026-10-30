"""SaúdePrática v1.9.101 no-regression / feature gates: run after apply_v120.py."""
from pathlib import Path
p=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app')
def check(path,*must):
    x=(p/path).read_text()
    for s in must:
        assert s in x,(path,s)
check('model/Models.kt','boxPhotoMode: String = "photo"','leafletDocumentId: String = ""')
check('data/DataRepository.kt','o.optString("box_photo_mode"','o.optString("leaflet_document_id"','.put("box_photo_mode",','.put("leaflet_document_id",')
check('MainActivity.kt','"Medicamento sem caixa" to "unboxed"','"Embalagem sem fotografia" to "missing"',
    'photoToLeafletPdf','HealthDocumentStore(this,profile)','DocumentOrientationActivity.VIEW_ONLY,true',
    'h.suspendedBadge.visibility=if(suspended)View.VISIBLE else View.GONE',
    'R.drawable.medicine_no_box','R.drawable.medicine_no_photo','h.card.alpha=if(completed)0.67f else 1f',
    'm.boxPhotoMode=chosenPhotoMode', '"📎 Anexar bula em PDF"','"📷 Digitalizar bula com a câmara → PDF"',
    '"🏥 Procurar unidade"','"📎 Importar guia"')
check('i18n/AppLanguage.kt','Medicamento sem caixa\tMedicine without a box','SUSPENSA\tSUSPENDED')
res=Path('build-src/MediAgenda_Android_v1/app/src/main/res/drawable-nodpi')
for name in ('medicine_no_box.jpg','medicine_no_photo.jpg'):
    f=res/name
    assert f.is_file() and f.stat().st_size>7000,name
    assert f.read_bytes().startswith(b'\xff\xd8'),name
print('PASS v1.9.101: images, med persistence, leaflets, catalog cards, suspended badge, compact agenda')
