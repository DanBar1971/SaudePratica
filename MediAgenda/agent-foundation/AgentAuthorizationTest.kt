package com.mediagenda.app.agent

/** Run without Android/Gradle: kotlinc AgentAuthorization.kt AgentAuthorizationTest.kt -include-runtime -d test.jar && java -jar test.jar */
fun main() {
    val unlocked = AgentSession(true, "regina", setOf("regina", "daniel"))
    check(AgentAuthorization.check(unlocked, AgentCommand.ReadAppointments("regina"))
        is AgentDecision.AllowRead)
    check(AgentAuthorization.check(unlocked, AgentCommand.PrepareMedicationDraft("regina"))
        is AgentDecision.ShowNativeDraft)
    check(AgentAuthorization.check(unlocked, AgentCommand.ReadMedications("daniel"))
        is AgentDecision.Deny) // authorized but NOT the selected profile
    check(AgentAuthorization.check(
        unlocked.copy(isUnlocked = false), AgentCommand.ReadAppointments("regina")
    ) is AgentDecision.Deny)
    check(AgentAuthorization.check(
        unlocked.copy(authorizedProfileIds = emptySet()), AgentCommand.ReadAppointments("regina")
    ) is AgentDecision.Deny)
    check(AgentAuthorization.check(unlocked, AgentCommand.DirectWrite("regina", "alterarDose"))
        is AgentDecision.Deny)
    check(AgentAuthorization.check(unlocked, AgentCommand.DirectWrite("regina", "TOMEI"))
        is AgentDecision.Deny)
    check(AgentAuthorization.check(unlocked, AgentCommand.ReadAppointments(""))
        is AgentDecision.Deny)
    println("OK: eight agent authorization / clinical safety checks")
}
