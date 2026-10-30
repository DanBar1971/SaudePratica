package com.mediagenda.app

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/** Privacy explanation surfaced from Health Connect's OS permission screen. */
class HealthPermissionsRationaleActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(42, 72, 42, 42)
            setBackgroundColor(Color.rgb(8, 30, 39))
        }
        val items = listOf(
            "SaúdePrática · Privacidade" to 25f,
            "Atividade e Saúde — Health Connect" to 19f,
            "Dados solicitados: passos, distância, calorias ativas e duração do sono. " +
                "A SaúdePrática pede apenas acesso de leitura, sujeito à tua autorização." to 16f,
            "Finalidade: mostrar um resumo diário e a evolução semanal da atividade no perfil que autorizares." to 16f,
            "Os dados são consultados localmente no Android quando abres ou atualizas o módulo. " +
                "Não são enviados para servidores, partilhados com terceiros, adicionados " +
                "ao backup da SaúdePrática nem utilizados para publicidade." to 16f,
            "Os dados do Health Connect pertencem ao utilizador deste telemóvel. " +
                "A SaúdePrática só os apresenta no perfil explicitamente associado. " +
                "Não é uma ligação à conta Google de familiares." to 16f,
            "Podes retirar as permissões em Definições → Health Connect → Permissões de aplicações → SaúdePrática." to 16f
        )
        items.forEach { (value, size) ->
            box.addView(TextView(this).apply {
                text = value; textSize = size; setTextColor(Color.WHITE)
                gravity = Gravity.START
                setPadding(0, 0, 0, 28)
            })
        }
        val scroll = ScrollView(this).apply { addView(box) }
        setContentView(scroll)
    }
}