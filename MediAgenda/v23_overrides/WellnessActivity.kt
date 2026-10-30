package com.mediagenda.app

import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.WellnessStore
import com.mediagenda.app.notifications.NotificationScheduler

/**
 * Wellbeing organizer: no medical diagnosis, no generated treatment or diet
 * plans. All user-entered prescriptions are stored only within the profile.
 */
class WellnessActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_PROFILE_ID = "profile_id"
        const val EXTRA_SECTION = "section"
    }

    private lateinit var profileId: String
    private lateinit var profileName: String
    private lateinit var store: WellnessStore
    private lateinit var content: LinearLayout
    private val turquoise = Color.rgb(0, 198, 190)
    private val dark = Color.rgb(5, 24, 33)
    private val lightText = Color.rgb(234, 247, 250)
    private val muted = Color.rgb(172, 204, 212)

    private fun dp(value: Int) = (value * resources.displayMetrics.density + 0.5f).toInt()
    private fun text(value: String, size: Float = 15f, bold: Boolean = false, color: Int = lightText) =
        TextView(this).apply {
            this.text = value
            textSize = size
            setTextColor(color)
            if (bold) setTypeface(null, Typeface.BOLD)
        }
    private fun panel() = GradientDrawable().apply {
        setColor(Color.rgb(24, 48, 59))
        cornerRadius = dp(20).toFloat()
        setStroke(dp(1), Color.rgb(42, 78, 83))
    }
    private fun button(label: String, onTap: () -> Unit) =
        MaterialButton(this).apply {
            text = label
            textSize = 14f
            isAllCaps = false
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(9, 114, 110))
            cornerRadius = dp(14)
            setOnClickListener { onTap() }
        }
    private fun line(parent: LinearLayout, value: String, size: Float = 15f,
                     bold: Boolean = false, color: Int = lightText, gap: Int = 8) {
        parent.addView(text(value, size, bold, color), LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = dp(gap)
        })
    }
    private fun card(parent: LinearLayout, title: String, description: String, actionLabel: String,
                     click: () -> Unit) {
        val shell = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(13), dp(16), dp(14))
            background = panel()
        }
        line(shell, title, 18f, true)
        line(shell, description, 13f, false, muted)
        shell.addView(button(actionLabel, click))
        parent.addView(shell, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            bottomMargin = dp(12)
        })
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val available = ProfileStore(this).all()
        val selected = available.firstOrNull { it.id == intent.getStringExtra(EXTRA_PROFILE_ID) }
            ?: available.singleOrNull()
        if (selected == null) { finish(); return }
        profileId = selected.id
        profileName = selected.name
        store = WellnessStore(this, profileId)
        window.statusBarColor = dark
        window.navigationBarColor = dark
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(17), dp(12), dp(17), dp(12))
            setBackgroundColor(dark)
        }
        val back = text("‹   SaúdePrática  /  Bem-estar", 17f, true, turquoise)
        back.setOnClickListener { finish() }
        root.addView(back)
        val scroller = ScrollView(this).apply {
            overScrollMode = View.OVER_SCROLL_NEVER
            clipToPadding = false
        }
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(15), 0, dp(26))
        }
        scroller.addView(content)
        root.addView(scroller, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(root)
        when (intent.getStringExtra(EXTRA_SECTION)) {
            "water" -> showWater()
            "glasses" -> showGlasses()
            "diet" -> showDiet()
            else -> showMenu()
        }
    }

    private fun heading(icon: String, title: String, subtitle: String) {
        content.removeAllViews()
        line(content, "$icon  $title", 24f, true)
        line(content, "$profileName · $subtitle", 13f, false, muted)
        line(content, "", 6f)
    }

    private fun showMenu() {
        heading("♡", "Cuidados pessoais", "Ferramentas por utilizador")
        card(content, "💧 Hidratação", "Registar copos de água e configurar lembretes opcionais.",
            "Abrir Hidratação", ::showWater)
        card(content, "👓 Graduação dos óculos", "Guardar dioptrias, cilindro, eixo e distância pupilar.",
            "Abrir Óculos", ::showGlasses)
        card(content, "🥗 Plano alimentar / regime",
            "Guardar as instruções alimentares indicadas pelo profissional de saúde, sobretudo durante tratamentos.",
            "Abrir Alimentação", ::showDiet)
    }

    private fun showWater() {
        heading("💧", "Beber água", "Avisos opcionais e registo diário")
        val amount = store.todayMl()
        val goal = store.optionalTargetMl
        card(content, "Hoje: $amount ml",
            if (goal > 0) "Objetivo escolhido: $goal ml" else "Sem objetivo diário obrigatório.",
            "🥛 Registar undefined ml") {
            store.recordGlass()
            showWater()
        }
        card(content, "Corrigir registo", "Retirar o último copo adicionado, se te enganaste.",
            "↶ Retirar undefined ml") {
            store.removeLastGlass()
            showWater()
        }
        val status = if (store.waterEnabled) {
            "Ligados: undefined–undefined, de undefined em undefined minutos."
        } else "Desligados. Não serão enviados avisos até ativares esta opção."
        card(content, "🔔 Avisos para beber água", status, "Configurar avisos") { configureWater() }
        line(content,
            "Se houver restrição de líquidos, doença renal ou cardíaca, segue o volume indicado pelo teu profissional de saúde. A aplicação não define automaticamente quanto deves beber.",
            12f, false, muted, 13)
    }

    private data class EditableField(val key: String, val edit: EditText)

    private fun field(form: LinearLayout, key: String, label: String, current: String,
                      multi: Boolean = false): EditableField {
        form.addView(text(label, 13f, true, Color.rgb(21, 82, 80)),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(12) })
        val input = EditText(this).apply {
            setText(current)
            textSize = 15f
            setSingleLine(!multi)
            if (multi) minLines = 3
            setTextColor(Color.rgb(20, 38, 47))
            setHintTextColor(Color.GRAY)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(10, 145, 138))
            if (multi) inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
            else inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
        }
        form.addView(input)
        return EditableField(key, input)
    }

    private fun dataDialog(title: String, fields: List<Triple<String, String, Boolean>>,
                           save: (Map<String, String>) -> Unit) {
        val form = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), dp(12))
        }
        val entries = fields.map { (key, label, multi) ->
            field(form, key, label, store.text(key), multi)
        }
        val scroller = ScrollView(this)
        scroller.addView(form)
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle(title).setView(scroller)
            .setPositiveButton("Guardar", null)
            .setNegativeButton("Cancelar", null)
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                save(entries.associate { it.key to it.edit.text.toString().trim() })
                dialog.dismiss()
            } catch (error: Exception) {
                Toast.makeText(this, error.message ?: "Não foi possível guardar.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun configureWater() {
        val choices = arrayOf("Desligar avisos", "Ativar avisos")
        val current = if (store.waterEnabled) 1 else 0
        MaterialAlertDialogBuilder(this)
            .setTitle("Lembretes de água")
            .setSingleChoiceItems(choices, current) { dialog, value ->
                dialog.dismiss()
                if (value == 0) {
                    store.saveWater(false, store.waterStart, store.waterEnd,
                        store.waterInterval, store.glassMl, store.optionalTargetMl)
                    NotificationScheduler(this).scheduleAllProfiles()
                    showWater()
                } else configureWaterTimes()
            }
            .setNeutralButton("Alterar horários e volume") { _, _ -> configureWaterTimes() }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun configureWaterTimes() {
        val form = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), 0, dp(18), dp(10))
        }
        val start = field(form, "start", "Primeiro aviso (HH:mm)", store.waterStart).edit
        val end = field(form, "end", "Último aviso (HH:mm)", store.waterEnd).edit
        val interval = field(form, "interval", "Intervalo em minutos (30–360)",
            store.waterInterval.toString()).edit
        val portion = field(form, "glass", "Quantidade registada por copo (ml)",
            store.glassMl.toString()).edit
        val target = field(form, "target", "Objetivo diário opcional em ml (0 = sem objetivo)",
            store.optionalTargetMl.toString()).edit
        val scroll = ScrollView(this)
        scroll.addView(form)
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("Configurar hidratação")
            .setMessage("Os avisos são opcionais. Os valores devem respeitar qualquer restrição de líquidos indicada pelo médico.")
            .setView(scroll)
            .setPositiveButton("Ativar e guardar", null)
            .setNegativeButton("Cancelar", null)
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                store.saveWater(true, start.text.toString().trim(), end.text.toString().trim(),
                    interval.text.toString().trim().toInt(),
                    portion.text.toString().trim().toInt(),
                    target.text.toString().trim().toInt())
                NotificationScheduler(this).scheduleAllProfiles()
                dialog.dismiss()
                showWater()
            } catch (error: Exception) {
                Toast.makeText(this, error.message ?: "Verifica os valores.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun showGlasses() {
        heading("👓", "Graduação dos óculos", "Receita óptica guardada localmente")
        val titles = listOf(
            "Olho direito" to listOf("right_sph" to "Esfera (SPH)", "right_cyl" to "Cilindro (CYL)", "right_axis" to "Eixo"),
            "Olho esquerdo" to listOf("left_sph" to "Esfera (SPH)", "left_cyl" to "Cilindro (CYL)", "left_axis" to "Eixo")
        )
        titles.forEach { (title, values) ->
            val description = values.joinToString(" · ") { (key, label) ->
                "$label: " + store.text(key).ifBlank { "—" }
            }
            card(content, title, description, "✎ Editar receita") { editGlasses() }
        }
        val extras = listOf("add" to "Adição (ADD)", "pd" to "Distância pupilar (DP)",
            "prescription_date" to "Data da receita", "optical_notes" to "Observações")
        card(content, "Outros dados", extras.joinToString("\n") { (key, label) ->
            "$label: " + store.text(key).ifBlank { "—" }
        }, "✎ Editar todos os dados") { editGlasses() }
        line(content, "Esta secção guarda os valores de uma receita óptica. Não mede a visão nem substitui a avaliação por um profissional.", 12f, false, muted)
    }

    private fun editGlasses() {
        dataDialog("Receita dos óculos", listOf(
            Triple("right_sph", "Olho direito — esfera (SPH)", false),
            Triple("right_cyl", "Olho direito — cilindro (CYL)", false),
            Triple("right_axis", "Olho direito — eixo (0–180°)", false),
            Triple("left_sph", "Olho esquerdo — esfera (SPH)", false),
            Triple("left_cyl", "Olho esquerdo — cilindro (CYL)", false),
            Triple("left_axis", "Olho esquerdo — eixo (0–180°)", false),
            Triple("add", "Adição (ADD)", false),
            Triple("pd", "Distância pupilar (mm)", false),
            Triple("prescription_date", "Data da receita", false),
            Triple("optical_notes", "Observações", true)
        )) { values ->
            listOf("right_axis", "left_axis").forEach { axis ->
                values[axis].orEmpty().replace(",", ".").takeIf { it.isNotBlank() }?.toDoubleOrNull()?.let {
                    require(it in 0.0..180.0) { "O eixo deve ser entre 0° e 180°." }
                }
            }
            store.saveText(values)
            showGlasses()
        }
    }

    private fun showDiet() {
        heading("🥗", "Alimentação e regime", "Indicações de um profissional de saúde")
        val items = listOf(
            "diet_name" to "Nome do plano",
            "diet_professional" to "Prescrito por",
            "diet_start" to "Início",
            "diet_end" to "Fim",
            "diet_instructions" to "Indicações do tratamento",
            "diet_allowed" to "Alimentos indicados",
            "diet_avoid" to "Restrições / alimentos a evitar",
            "diet_notes" to "Outras observações"
        )
        val summary = items.joinToString("\n\n") { (key, title) ->
            "$title\n" + store.text(key).ifBlank { "Não definido" }
        }
        card(content, "Plano alimentar pessoal", summary, "✎ Guardar ou alterar plano") {
            dataDialog("Plano alimentar do tratamento", listOf(
                Triple("diet_name", "Nome do plano / tratamento", false),
                Triple("diet_professional", "Médico ou nutricionista responsável", false),
                Triple("diet_start", "Data de início", false),
                Triple("diet_end", "Data de fim", false),
                Triple("diet_instructions", "Indicações dadas pelo profissional", true),
                Triple("diet_allowed", "Alimentos permitidos / preferidos", true),
                Triple("diet_avoid", "Alimentos proibidos ou a evitar", true),
                Triple("diet_notes", "Outras notas", true)
            )) { values ->
                store.saveText(values)
                showDiet()
            }
        }
        line(content,
            "A aplicação regista as orientações que recebeste. Não cria dietas clínicas nem altera restrições prescritas. Antes de mudar a alimentação durante um tratamento, confirma com a tua equipa de saúde.",
            12f, false, muted, 13)
    }
}
