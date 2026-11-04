package com.mediagenda.app.agent

/**
 * A local LLM may suggest a command, but never receives a data-store handle.
 * The Android UI remains the only writer of clinical records and alarms.
 */
sealed interface AgentCommand {
    val profileId: String

    data class ReadAppointments(override val profileId: String) : AgentCommand
    data class ReadMedications(override val profileId: String) : AgentCommand
    data class PrepareAppointmentDraft(override val profileId: String) : AgentCommand
    data class PrepareMedicationDraft(override val profileId: String) : AgentCommand
    data class OpenHelp(override val profileId: String) : AgentCommand

    // Explicitly model unsupported requests so a model cannot smuggle them
    // into a draft or read function.
    data class DirectWrite(override val profileId: String, val operation: String) : AgentCommand
}

data class AgentSession(
    val isUnlocked: Boolean,
    val selectedProfileId: String,
    val authorizedProfileIds: Set<String>
)

sealed interface AgentDecision {
    data class AllowRead(val command: AgentCommand) : AgentDecision
    data class ShowNativeDraft(val command: AgentCommand) : AgentDecision
    data class Deny(val reason: String) : AgentDecision
}

/** Pure function; call again immediately before executing the tool. */
object AgentAuthorization {
    fun check(session: AgentSession, command: AgentCommand): AgentDecision {
        if (!session.isUnlocked) return AgentDecision.Deny("É necessário desbloquear a aplicação.")
        if (session.selectedProfileId.isBlank() || command.profileId.isBlank()) {
            return AgentDecision.Deny("Seleciona um perfil válido.")
        }
        if (command.profileId != session.selectedProfileId) {
            return AgentDecision.Deny("O pedido não pertence ao perfil selecionado.")
        }
        if (!session.authorizedProfileIds.contains(command.profileId)) {
            return AgentDecision.Deny("Não tens autorização para consultar este perfil.")
        }
        return when (command) {
            is AgentCommand.ReadAppointments,
            is AgentCommand.ReadMedications,
            is AgentCommand.OpenHelp -> AgentDecision.AllowRead(command)
            is AgentCommand.PrepareAppointmentDraft,
            is AgentCommand.PrepareMedicationDraft -> AgentDecision.ShowNativeDraft(command)
            is AgentCommand.DirectWrite -> AgentDecision.Deny(
                "Alterações clínicas e alarmes exigem confirmação na ficha original."
            )
        }
    }
}
