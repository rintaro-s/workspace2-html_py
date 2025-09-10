class ServerMember < ApplicationRecord
  self.table_name = 'server_members'

  def self.members_payload!(server_id, viewer)
    unless where(server_id: server_id, user_id: viewer.id).exists?
      return { members: [] }
    end
    rows = 
      joins("JOIN users u ON u.id = server_members.user_id")
      .where(server_id: server_id)
      .order(:joined_at)
      .pluck('u.id', 'u.username', 'u.nickname', 'u.avatar', 'server_members.role', 'server_members.joined_at')

    { members: rows.map { |id, username, nickname, avatar, role, joined_at|
      {
        id: id,
        username: username,
        nickname: nickname.presence || username,
        avatar: avatar,
        role: role,
        joinedAt: joined_at
      }
    } }
  end
end
