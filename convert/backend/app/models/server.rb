class Server < ApplicationRecord
  self.table_name = 'servers'

  def self.gen_id
    "server_#{(Time.now.to_f * 1000).to_i}"
  end
end
