class InitSchema < ActiveRecord::Migration[7.1]
  def change
    create_table :users do |t|
      t.string :username, null: false, index: { unique: true }
      t.string :password_hash, null: false
      t.string :nickname
      t.string :email
      t.integer :admission_year
      t.integer :graduation_year
      t.string :major
      t.string :student_id
      t.text :bio
      t.string :avatar
      t.string :ui_scale, default: 'medium'
      t.string :theme, default: 'dark'
      t.string :language, default: 'ja'
      t.string :timezone, default: 'Asia/Tokyo'
      t.text :notification_settings, default: '{}'
      t.text :privacy_settings, default: '{}'
      t.datetime :last_login
      t.boolean :is_active, default: true
      t.timestamps
    end

    create_table :servers, id: false do |t|
      t.string :id, primary_key: true
      t.string :name, null: false
      t.text :description
      t.string :icon, null: false
      t.string :banner
      t.integer :owner_id
      t.boolean :is_public, default: false
      t.string :invite_code, index: { unique: true }
      t.integer :max_members, default: 100
      t.text :settings, default: '{}'
      t.timestamps
    end

    create_table :server_members do |t|
      t.string :server_id, null: false
      t.integer :user_id, null: false
      t.string :role, default: 'member'
      t.datetime :joined_at, default: -> { 'CURRENT_TIMESTAMP' }
      t.integer :invited_by
      t.text :permissions, default: '{}'
      t.index [:server_id, :user_id], unique: true
    end

    create_table :server_invites, id: false do |t|
      t.string :id, primary_key: true
      t.string :server_id, null: false
      t.integer :inviter_id, null: false
      t.string :invitee_email
      t.string :invitee_username
      t.string :invite_code, null: false, index: { unique: true }
      t.datetime :expires_at
      t.datetime :used_at
      t.integer :used_by
      t.integer :max_uses, default: 1
      t.integer :current_uses, default: 0
      t.datetime :created_at, default: -> { 'CURRENT_TIMESTAMP' }
    end

    create_table :password_recovery do |t|
      t.integer :user_id, null: false
      t.integer :recovery_partner_id, null: false
      t.string :status, default: 'pending'
      t.string :request_type, default: 'reset'
      t.integer :initiated_by, null: false
      t.string :recovery_token
      t.datetime :expires_at
      t.datetime :approved_at
      t.datetime :completed_at
      t.datetime :created_at, default: -> { 'CURRENT_TIMESTAMP' }
      t.index [:user_id, :recovery_partner_id], unique: true
    end

    create_table :files, id: false do |t|
      t.string :id, primary_key: true
      t.string :filename, null: false
      t.string :original_filename, null: false
      t.string :file_path, null: false
      t.integer :file_size, null: false
      t.string :mime_type, null: false
      t.integer :upload_by, null: false
      t.string :server_id
      t.string :feature_id
      t.boolean :is_public, default: false
      t.integer :download_count, default: 0
      t.datetime :created_at, default: -> { 'CURRENT_TIMESTAMP' }
    end

    create_table :features, id: false do |t|
      t.string :id, primary_key: true
      t.string :server_id, null: false
      t.string :name, null: false
      t.string :type, null: false
      t.string :icon, null: false
      t.integer :position, default: 0
      t.datetime :created_at, default: -> { 'CURRENT_TIMESTAMP' }
    end

    create_table :feature_content, id: false do |t|
      t.string :feature_id, primary_key: true
      t.text :content, null: false
      t.datetime :updated_at, default: -> { 'CURRENT_TIMESTAMP' }
    end

    create_table :sessions, id: false do |t|
      t.string :session_id, primary_key: true
      t.integer :user_id, null: false
      t.datetime :created_at, default: -> { 'CURRENT_TIMESTAMP' }
      t.datetime :expires_at, null: false
    end
  end
end
