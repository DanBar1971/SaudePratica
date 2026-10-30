from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
p=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.5 UI missing "+label)
 s=s.replace(old,new,1)

# MainActivity keeps one route at a time. Dashboard is the only menu;
# reserve the complete height for the content and navigate via the header.
edit('''    private lateinit var bottomNav: LinearLayout''',
'''    private lateinit var bottomNav: LinearLayout
    private var currentScreen = "Início"''', "currentScreen")
edit('''        root.addView(bottomNav, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(76)))''',
'''        // The dashboard already contains all the modules. Do not duplicate
        // those same buttons at the bottom of every screen.
        bottomNav.visibility = View.GONE''', "hide duplicate bar")
edit('''    private fun renderBottomNav(selected: Int) {
        bottomNav.removeAllViews()''',
'''    private fun renderBottomNav(selected: Int) {
        bottomNav.visibility = View.GONE
        return
        bottomNav.removeAllViews()''', "disable bottom navigation")

edit('''    private fun screenHeader(icon: String, title: String, subtitle: String) {
        val top = LinearLayout(this).apply {''',
'''    private fun screenHeader(icon: String, title: String, subtitle: String) {
        currentScreen = title
        val top = LinearLayout(this).apply {''', "track active route")
edit('''        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }''',
'''        if (title != "Início") {
            top.addView(TextView(this).apply {
                text = "‹"
                textSize = 35f
                gravity = Gravity.CENTER
                setTextColor(primaryDark)
                contentDescription = "Voltar ao Início"
                setOnClickListener { showHome() }
            }, LinearLayout.LayoutParams(dp(34), dp(60)))
        }
        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }''', "header home arrow")
edit('''        super.onCreate(savedInstanceState)
        // Migrate the original user's files''',
'''        super.onCreate(savedInstanceState)
        onBackPressedDispatcher.addCallback(this, object : androidx.activity.OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (currentScreen != "Início") showHome()
                else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
        // Migrate the original user's files''', "back to dashboard")
# do not show arrow in first-run user selection.
edit('''    private fun showProfileSelection() {
        val available = profiles.all()''',
'''    private fun showProfileSelection() {
        currentScreen = "Escolher utilizador"
        val available = profiles.all()''', "profile chooser route")
# Dropdown for account is still clickable but bottom nav hidden.
p.write_text(s,encoding="utf-8")
print("v1.9.5 UI: remove redundant bottom menu, navigate via header/back.")
