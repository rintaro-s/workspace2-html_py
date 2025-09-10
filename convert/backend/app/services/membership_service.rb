class MembershipService
  def initialize(user)
    @user = user
  end

  def update_role!(server_id, target_user_id, new_role)
    raise '必要なパラメータが不足しています' if [server_id, target_user_id, new_role].any?(&:blank?)
    raise '無効なロールです' unless %w[member moderator admin].include?(new_role)
    admin = ServerMember.find_by(server_id: server_id, user_id: @user.id)
    raise 'ロールを変更する権限がありません' unless admin&.role.in?(['owner','admin'])
    sm = ServerMember.find_by!(server_id: server_id, user_id: target_user_id)
    sm.update!(role: new_role)
  end

  def kick!(server_id, target_user_id)
    raise '必要なパラメータが不足しています' if [server_id, target_user_id].any?(&:blank?)
    admin = ServerMember.find_by(server_id: server_id, user_id: @user.id)
    raise 'メンバーをキックする権限がありません' unless admin&.role.in?(['owner','admin'])
    sm = ServerMember.find_by!(server_id: server_id, user_id: target_user_id)
    raise 'オーナーはキックできません' if sm.role == 'owner'
    sm.destroy!
  end
end
