require_relative 'boot'
require 'rails/all'

Bundler.require(*Rails.groups)

module ApiCompat
  class Application < Rails::Application
    config.load_defaults 7.1
    config.api_only = true

    # CORS (Next.js からの Cookie 同送を許可)
    config.middleware.insert_before 0, Rack::Cors do
      allow do
        origins /localhost:3000$/
        resource '*', headers: :any, methods: [:get, :post, :options], credentials: true
      end
    end

    # セッションをAPIモードで使う
    config.middleware.use ActionDispatch::Cookies
    config.middleware.use ActionDispatch::Session::CookieStore, key: '_circle_platform_session', same_site: :lax
  end
end
