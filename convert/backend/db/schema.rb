# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.1].define(version: 2025_01_01_000000) do
  create_table "feature_content", primary_key: "feature_id", id: :string, force: :cascade do |t|
    t.text "content", null: false
    t.datetime "updated_at", default: -> { "CURRENT_TIMESTAMP" }
  end

  create_table "features", id: :string, force: :cascade do |t|
    t.string "server_id", null: false
    t.string "name", null: false
    t.string "type", null: false
    t.string "icon", null: false
    t.integer "position", default: 0
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }
  end

  create_table "files", id: :string, force: :cascade do |t|
    t.string "filename", null: false
    t.string "original_filename", null: false
    t.string "file_path", null: false
    t.integer "file_size", null: false
    t.string "mime_type", null: false
    t.integer "upload_by", null: false
    t.string "server_id"
    t.string "feature_id"
    t.boolean "is_public", default: false
    t.integer "download_count", default: 0
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }
  end

  create_table "password_recovery", force: :cascade do |t|
    t.integer "user_id", null: false
    t.integer "recovery_partner_id", null: false
    t.string "status", default: "pending"
    t.string "request_type", default: "reset"
    t.integer "initiated_by", null: false
    t.string "recovery_token"
    t.datetime "expires_at"
    t.datetime "approved_at"
    t.datetime "completed_at"
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }
    t.index ["user_id", "recovery_partner_id"], name: "index_password_recovery_on_user_id_and_recovery_partner_id", unique: true
  end

  create_table "server_invites", id: :string, force: :cascade do |t|
    t.string "server_id", null: false
    t.integer "inviter_id", null: false
    t.string "invitee_email"
    t.string "invitee_username"
    t.string "invite_code", null: false
    t.datetime "expires_at"
    t.datetime "used_at"
    t.integer "used_by"
    t.integer "max_uses", default: 1
    t.integer "current_uses", default: 0
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }
    t.index ["invite_code"], name: "index_server_invites_on_invite_code", unique: true
  end

  create_table "server_members", force: :cascade do |t|
    t.string "server_id", null: false
    t.integer "user_id", null: false
    t.string "role", default: "member"
    t.datetime "joined_at", default: -> { "CURRENT_TIMESTAMP" }
    t.integer "invited_by"
    t.text "permissions", default: "{}"
    t.index ["server_id", "user_id"], name: "index_server_members_on_server_id_and_user_id", unique: true
  end

  create_table "servers", id: :string, force: :cascade do |t|
    t.string "name", null: false
    t.text "description"
    t.string "icon", null: false
    t.string "banner"
    t.integer "owner_id"
    t.boolean "is_public", default: false
    t.string "invite_code"
    t.integer "max_members", default: 100
    t.text "settings", default: "{}"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["invite_code"], name: "index_servers_on_invite_code", unique: true
  end

  create_table "sessions", primary_key: "session_id", id: :string, force: :cascade do |t|
    t.integer "user_id", null: false
    t.datetime "created_at", default: -> { "CURRENT_TIMESTAMP" }
    t.datetime "expires_at", null: false
  end

  create_table "users", force: :cascade do |t|
    t.string "username", null: false
    t.string "password_hash", null: false
    t.string "nickname"
    t.string "email"
    t.integer "admission_year"
    t.integer "graduation_year"
    t.string "major"
    t.string "student_id"
    t.text "bio"
    t.string "avatar"
    t.string "ui_scale", default: "medium"
    t.string "theme", default: "dark"
    t.string "language", default: "ja"
    t.string "timezone", default: "Asia/Tokyo"
    t.text "notification_settings", default: "{}"
    t.text "privacy_settings", default: "{}"
    t.datetime "last_login"
    t.boolean "is_active", default: true
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["username"], name: "index_users_on_username", unique: true
  end

end
