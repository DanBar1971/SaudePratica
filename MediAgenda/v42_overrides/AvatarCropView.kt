package com.mediagenda.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.RectF
import android.view.MotionEvent
import android.view.View
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.min

/**
 * On-device square avatar crop. The crop square is stored (not a circular
 * mask) so existing circular avatar renderers can display it correctly.
 *
 * Supports drag, pinch zoom, +/- buttons and 90-degree rotation. It never
 * uploads anything or changes the saved avatar until the user confirms.
 */
class AvatarCropView(context:Context, private var original:Bitmap):View(context){
    private val imagePaint=Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private val overlay=Paint(Paint.ANTI_ALIAS_FLAG).apply{color=0xA6000000.toInt()}
    private val border=Paint(Paint.ANTI_ALIAS_FLAG).apply{
        color=Color.WHITE
        style=Paint.Style.STROKE
        strokeWidth=dp(2f)
    }
    private val circlePaint=Paint(Paint.ANTI_ALIAS_FLAG).apply{
        color=0xB8FFFFFF.toInt()
        style=Paint.Style.STROKE
        strokeWidth=dp(1.25f)
    }
    private val backgroundPaint=Paint().apply{color=Color.rgb(12,27,35)}
    private var rotation=0
    private var activeBitmap:Bitmap=original
    private var zoom=1f
    private var offsetX=0f
    private var offsetY=0f
    private var lastX=0f
    private var lastY=0f
    private var lastDistance=0f
    private var trackingPinch=false
    private val square=RectF()
    private var baseScale=1f

    private fun dp(v:Float)=v*resources.displayMetrics.density

    override fun onSizeChanged(w:Int,h:Int,oldw:Int,oldh:Int){
        super.onSizeChanged(w,h,oldw,oldh)
        val side=(min(w,h)-dp(20f)).coerceAtLeast(1f)
        square.set((w-side)/2f,(h-side)/2f,(w+side)/2f,(h+side)/2f)
        updateScale()
    }

    private fun updateScale(){
        if(square.width()<=0f)return
        baseScale=square.width()/min(activeBitmap.width,activeBitmap.height).toFloat()
        constrainOffset()
    }

    private fun constrainOffset(){
        val s=baseScale*zoom
        val limitX=((activeBitmap.width*s-square.width())/2f).coerceAtLeast(0f)
        val limitY=((activeBitmap.height*s-square.height())/2f).coerceAtLeast(0f)
        offsetX=offsetX.coerceIn(-limitX,limitX)
        offsetY=offsetY.coerceIn(-limitY,limitY)
    }

    private fun positionMatrix():Matrix{
        val s=baseScale*zoom
        return Matrix().apply{
            postScale(s,s)
            postTranslate(width/2f-activeBitmap.width*s/2f+offsetX,
                          height/2f-activeBitmap.height*s/2f+offsetY)
        }
    }

    override fun onDraw(canvas:Canvas){
        super.onDraw(canvas)
        canvas.drawRect(0f,0f,width.toFloat(),height.toFloat(),backgroundPaint)
        if(square.width()<=0f)return
        canvas.save()
        canvas.clipRect(square)
        canvas.drawBitmap(activeBitmap,positionMatrix(),imagePaint)
        canvas.restore()
        // Dim areas outside the crop frame; round guide helps avatar layout.
        canvas.drawRect(0f,0f,width.toFloat(),square.top,overlay)
        canvas.drawRect(0f,square.bottom,width.toFloat(),height.toFloat(),overlay)
        canvas.drawRect(0f,square.top,square.left,square.bottom,overlay)
        canvas.drawRect(square.right,square.top,width.toFloat(),square.bottom,overlay)
        canvas.drawRoundRect(square,dp(5f),dp(5f),border)
        val radius=square.width()/2f-dp(5f)
        canvas.drawCircle(square.centerX(),square.centerY(),radius,circlePaint)
    }

    override fun onTouchEvent(event:MotionEvent):Boolean {
        when(event.actionMasked){
            MotionEvent.ACTION_DOWN->{
                lastX=event.x;lastY=event.y
                trackingPinch=false
                parent?.requestDisallowInterceptTouchEvent(true)
                return true
            }
            MotionEvent.ACTION_POINTER_DOWN->{
                if(event.pointerCount>=2){
                    lastDistance=distance(event)
                    trackingPinch=true
                }
                return true
            }
            MotionEvent.ACTION_MOVE->{
                if(event.pointerCount>=2){
                    val d=distance(event)
                    if(d>0f&&lastDistance>0f){
                        zoom=(zoom*(d/lastDistance)).coerceIn(1f,6f)
                        lastDistance=d
                        constrainOffset()
                    }
                    trackingPinch=true
                }else if(!trackingPinch){
                    offsetX+=event.x-lastX
                    offsetY+=event.y-lastY
                    constrainOffset()
                }
                lastX=event.x;lastY=event.y
                invalidate()
                return true
            }
            MotionEvent.ACTION_POINTER_UP->{
                trackingPinch=true
                return true
            }
            MotionEvent.ACTION_UP,MotionEvent.ACTION_CANCEL->{
                trackingPinch=false
                parent?.requestDisallowInterceptTouchEvent(false)
                performClick()
                return true
            }
        }
        return true
    }
    private fun distance(event:MotionEvent):Float =
        hypot(event.getX(0)-event.getX(1),event.getY(0)-event.getY(1))

    override fun performClick():Boolean{
        super.performClick()
        return true
    }

    fun setZoom(factor:Float){
        zoom=(zoom*factor).coerceIn(1f,6f)
        constrainOffset()
        invalidate()
    }
    fun resetCrop(){
        zoom=1f
        offsetX=0f;offsetY=0f
        constrainOffset()
        invalidate()
    }
    fun rotateRight(){
        rotation=(rotation+90)%360
        if(activeBitmap!==original)activeBitmap.recycle()
        activeBitmap=if(rotation==0)original else Bitmap.createBitmap(
            original,0,0,original.width,original.height,
            Matrix().apply{postRotate(rotation.toFloat())},true)
        resetCrop()
        updateScale()
        invalidate()
    }
    fun makeSquare(size:Int=900):Bitmap{
        require(square.width()>0f && size in 128..2048){
            "Aguarda até a imagem aparecer para confirmar."
        }
        val output=Bitmap.createBitmap(size,size,Bitmap.Config.ARGB_8888)
        val canvas=Canvas(output)
        canvas.drawColor(Color.WHITE)
        val scale=size.toFloat()/square.width()
        val transform=positionMatrix()
        transform.postTranslate(-square.left,-square.top)
        transform.postScale(scale,scale)
        canvas.drawBitmap(activeBitmap,transform,imagePaint)
        return output
    }
    fun release(){
        if(activeBitmap!==original)activeBitmap.recycle()
        original.recycle()
    }
}
