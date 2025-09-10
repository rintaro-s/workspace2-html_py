class PasswordRecoveryService
  def self.request!(username, partner_username)
    raise 'ユーザー名とパートナーのユーザー名が必要です' if username.blank? || partner_username.blank?
    user = User.find_by(username: username)
    partner = User.find_by(username: partner_username)
    raise 'ユーザーが見つかりません' unless user && partner
    existing = PasswordRecovery.where(user_id: user.id, recovery_partner_id: partner.id, status: 'pending').first
    raise '既にパスワード復旧リクエストが存在します' if existing
    token = SecureRandom.urlsafe_base64(32)
    PasswordRecovery.create!(user_id: user.id, recovery_partner_id: partner.id, initiated_by: user.id, recovery_token: token, expires_at: 24.hours.from_now)
    { success: true, data: { message: 'パスワード復旧リクエストを送信しました', recoveryToken: token } }
  end

  def self.approve!(approver, token)
    raise '復旧トークンが必要です' if token.blank?
    pr = PasswordRecovery.where(recovery_token: token, recovery_partner_id: approver.id, status: 'pending').first
    raise '無効な復旧トークンです' unless pr
    pr.update!(status: 'approved', approved_at: Time.current)
    { success: true, data: { message: 'パスワード復旧を承認しました' } }
  end

  def self.reset!(token, new_password)
    raise '復旧トークンと新パスワードが必要です' if token.blank? || new_password.blank?
    raise 'パスワードは6文字以上にしてください' if new_password.length < 6
    pr = PasswordRecovery.where("recovery_token = ? AND status = 'approved' AND expires_at > CURRENT_TIMESTAMP", token).first
    raise '無効または期限切れの復旧トークンです' unless pr
    user = User.find(pr.user_id)
    user.update!(password_hash: User.sha256(new_password))
    pr.update!(status: 'completed', completed_at: Time.current)
    { success: true, data: { message: 'パスワードをリセットしました' } }
  end
end
