package com.mediagenda.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import org.tensorflow.lite.DataType
import org.tensorflow.lite.Interpreter
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Locale

/** Offline Google AIY Food classifier (Apache-2.0, 2023 food dishes).
 * Dishes are suggestions only: this model CANNOT determine ingredients, allergens or nutrition.
 * Neither photos nor inferences are transmitted.
 */
internal class FoodDishClassifier(private val context: Context) {
    data class Guess(val dish: String, val score: Float)
    fun identify(bitmap: Bitmap): List<Guess> {
        val raw = context.assets.open("saude_food_v1.tflite").use { it.readBytes() }
        val model = ByteBuffer.allocateDirect(raw.size).order(ByteOrder.nativeOrder())
        model.put(raw); model.rewind()
        val labels = context.assets.open("saude_food_labels.csv").bufferedReader().use { reader ->
            reader.readLines().drop(1).mapNotNull { line ->
                val idx=line.indexOf(',')
                if (idx < 1) null else line.substring(idx+1).trim().trim('"')
            }
        }
        Interpreter(model, Interpreter.Options().setNumThreads(2)).use { interpreter ->
            val inputTensor = interpreter.getInputTensor(0)
            val shape = inputTensor.shape()
            require(shape.size == 4 && shape[0] == 1 && shape[3] == 3) { "Formato de modelo incompatível" }
            val w = shape[2]; val h = shape[1]
            require(w in 100..512 && h in 100..512) { "Dimensões de imagem inválidas" }
            val scaled = Bitmap.createScaledBitmap(bitmap, w, h, true)
            val pix=IntArray(w*h)
            scaled.getPixels(pix, 0, w, 0, 0, w, h)
            if (scaled !== bitmap) scaled.recycle()
            val ib=ByteBuffer.allocateDirect(inputTensor.numBytes()).order(ByteOrder.nativeOrder())
            val inputFloat=inputTensor.dataType()==DataType.FLOAT32
            require(inputFloat || inputTensor.dataType()==DataType.UINT8) { "Entrada não suportada" }
            for (color in pix) {
                if (inputFloat) {
                    ib.putFloat(Color.red(color)/255f)
                    ib.putFloat(Color.green(color)/255f)
                    ib.putFloat(Color.blue(color)/255f)
                } else {
                    ib.put(Color.red(color).toByte())
                    ib.put(Color.green(color).toByte())
                    ib.put(Color.blue(color).toByte())
                }
            }
            ib.rewind()
            val out=interpreter.getOutputTensor(0)
            val ob=ByteBuffer.allocateDirect(out.numBytes()).order(ByteOrder.nativeOrder())
            interpreter.run(ib,ob); ob.rewind()
            val n=out.numElements()
            require(n in 10..10000) { "Número de resultados inválido" }
            val scores=FloatArray(n)
            when(out.dataType()) {
                DataType.FLOAT32 -> for(i in 0 until n) scores[i]=ob.float
                DataType.UINT8 -> {
                    val q=out.quantizationParams()
                    for(i in 0 until n) scores[i]=((ob.get().toInt() and 255)-q.zeroPoint)*q.scale
                }
                else -> error("Resultados do modelo incompatíveis")
            }
            // The published labelmap has class 0=background, 1..2023=food.
            return (1 until minOf(n,labels.size)).asSequence()
                .map { Guess(labels[it], scores[it]) }
                .filter { it.score.isFinite() && it.score>0f && it.dish.isNotBlank() }
                .sortedByDescending { it.score }.take(5).toList()
        }
    }
}