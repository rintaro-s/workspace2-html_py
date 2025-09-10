class InviteService
  def initialize(user)
    @user = user
  end

  def create!(server_id)
    raise 'サーバーIDが必要です' if server_id.blank?
    membership = ServerMember.find_by(server_id: server_id, user_id: @user.id)
    return render_error('招待する権限がありません') unless membership&.role.in?(['owner','admin'])

    invite = ServerInvite.create!(
      id: SecureRandom.uuid,
      server_id: server_id,
      inviter_id: @user.id,
      invite_code: SecureRandom.urlsafe_base64(8),
      expires_at: 24.hours.from_now
    )
    { success: true, data: { inviteId: invite.id, inviteCode: invite.invite_code, expiresAt: invite.expires_at.iso8601 } }
  end

  def accept!(invite_code)
    invite = ServerInvite.where('invite_code = ? AND used_at IS NULL AND expires_at > CURRENT_TIMESTAMP', invite_code).first
    raise '無効または期限切れの招待コードです' unless invite
    return if ServerMember.exists?(server_id: invite.server_id, user_id: @user.id)
    ServerMember.create!(server_id: invite.server_id, user_id: @user.id, role: 'member', invited_by: invite.inviter_id)
    invite.update!(used_at: Time.current, used_by: @user.id, current_uses: (invite.current_uses || 0) + 1)
  end

  private
  def render_error(msg)
    raise StandardError, msg
  end
end
