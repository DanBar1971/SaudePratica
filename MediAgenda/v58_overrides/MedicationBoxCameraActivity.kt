package com.mediagenda.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File

/** In-app camera: sidesteps OEM ACTION_IMAGE_CAPTURE / TakePicture result bugs.
 * The only successful RESULT_OK is after CameraX has written a valid JPEG to
 * the app's private medical-photo folder. Nothing is saved to a medical record
 * without a later explicit confirmation in MainActivity.
 */
class MedicationBoxCameraActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_CAPTURED_FILE = "captured_medication_box_file"
        private const val STATE_FILE = "saudepratica_camera_capture_v1"
    }
    private lateinit var previewView:PreviewView
    private lateinit var shutter:Button
    private lateinit var message:TextView
    private var imageCapture:ImageCapture?=null
    private var captureInProgress=false

    private val cameraPermission=registerForActivityResult(
        ActivityResultContracts.RequestPermission()) { granted ->
        if(granted)startCamera() else {
            message.text="Sem autorização para a câmara. Podes usar uma fotografia da galeria."
            shutter.isEnabled=false
        }
    }

    private fun dp(n:Int):Int=(n*resources.displayMetrics.density+.5f).toInt()
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        // Keep the existing app PIN and other user privacy settings untouched.
        val root=FrameLayout(this).apply{setBackgroundColor(Color.BLACK)}
        previewView=PreviewView(this).apply{
            implementationMode=PreviewView.ImplementationMode.COMPATIBLE
            scaleType=PreviewView.ScaleType.FIT_CENTER
        }
        root.addView(previewView,FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT))
        val controls=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            gravity=Gravity.CENTER_HORIZONTAL
            setPadding(dp(12),dp(12),dp(12),dp(32))
            setBackgroundColor(0xD91A2531.toInt())
        }
        val title=TextView(this).apply{
            text="Fotografar caixa de medicamento"
            textSize=18f;setTextColor(Color.WHITE)
            setTypeface(null,Typeface.BOLD)
            gravity=Gravity.CENTER
        }
        controls.addView(title)
        message=TextView(this).apply{
            text="Enquadra o nome e a dosagem. A foto será guardada na SaúdePrática."
            textSize=14f;setTextColor(Color.WHITE)
            gravity=Gravity.CENTER
            setPadding(dp(5),dp(8),dp(5),dp(8))
        }
        controls.addView(message)
        shutter=Button(this).apply{
            text="📸 TIRAR FOTOGRAFIA"
            isEnabled=false
            setOnClickListener{capture()}
        }
        controls.addView(shutter,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,dp(56)))
        val cancel=Button(this).apply{
            text="Cancelar"
            setOnClickListener{finish()}
        }
        controls.addView(cancel,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,dp(48)))
        root.addView(controls,FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT,
            Gravity.BOTTOM))
        setContentView(root)
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)==
            PackageManager.PERMISSION_GRANTED)startCamera()
        else cameraPermission.launch(Manifest.permission.CAMERA)
    }
    private fun startCamera() {
        message.text="A iniciar câmara..."
        val future=ProcessCameraProvider.getInstance(this)
        future.addListener({
            if(isFinishing||isDestroyed)return@addListener
            runCatching{
                val provider=future.get()
                val preview=Preview.Builder().build()
                val capture=ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                    .build()
                preview.setSurfaceProvider(previewView.surfaceProvider)
                provider.unbindAll()
                provider.bindToLifecycle(this,CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,capture)
                imageCapture=capture
                shutter.isEnabled=true
                message.text="Enquadra o nome e a dosagem e toca em Tirar fotografia."
            }.onFailure{e->
                message.text="Não foi possível iniciar a câmara: ${e.localizedMessage}"
                shutter.isEnabled=false
            }
        },ContextCompat.getMainExecutor(this))
    }
    private fun capture(){
        val camera=imageCapture?:return
        if(captureInProgress)return
        captureInProgress=true
        shutter.isEnabled=false
        message.text="A guardar fotografia..."
        val folder=File(filesDir,"medication_photos").apply{mkdirs()}
        val file=File(folder,"medicamento_${System.currentTimeMillis()}.jpg")
        val output=ImageCapture.OutputFileOptions.Builder(file).build()
        camera.takePicture(output,ContextCompat.getMainExecutor(this),
            object:ImageCapture.OnImageSavedCallback{
                override fun onImageSaved(result:ImageCapture.OutputFileResults){
                    val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                    if(file.isFile&&file.length()>1024){
                        BitmapFactory.decodeFile(file.absolutePath,bounds)
                    }
                    if(bounds.outWidth<40||bounds.outHeight<40){
                        file.delete()
                        fail("A câmara não conseguiu gravar uma imagem válida. Tenta outra vez.")
                        return
                    }
                    // Save last known *valid* capture for recovery, even if the
                    // MainActivity is killed as we close this Activity.
                    getSharedPreferences(STATE_FILE,MODE_PRIVATE).edit()
                        .putString("latest_internal_camera_file",file.absolutePath)
                        .putLong("latest_internal_camera_time",System.currentTimeMillis())
                        .commit()
                    setResult(Activity.RESULT_OK,Intent().putExtra(EXTRA_CAPTURED_FILE,
                        file.absolutePath))
                    finish()
                }
                override fun onError(error:ImageCaptureException){
                    file.delete()
                    fail("Erro ao captar fotografia: ${error.localizedMessage}")
                }
            })
    }
    private fun fail(text:String){
        captureInProgress=false
        shutter.isEnabled=imageCapture!=null
        message.text=text
        Toast.makeText(this,text,Toast.LENGTH_LONG).show()
    }
}