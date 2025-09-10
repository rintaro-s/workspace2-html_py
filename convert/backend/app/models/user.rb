require 'digest'

class User < ApplicationRecord
  self.table_name = 'users'

  def self.sha256(str)
    Digest::SHA256.hexdigest(str)
  end
end
