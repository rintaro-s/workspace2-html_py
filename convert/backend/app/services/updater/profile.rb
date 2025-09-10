module Updater
  class Profile
    def self.update!(user, params)
      fields = {}
      fields[:nickname] = params[:nickname] if params[:nickname].present?
      fields[:email] = params[:email] if params[:email].present?
      fields[:admission_year] = params[:admission_year].to_i if params[:admission_year].present?
      fields[:graduation_year] = params[:graduation_year].to_i if params[:graduation_year].present?
      fields[:major] = params[:major] if params[:major].present?
      fields[:student_id] = params[:student_id] if params[:student_id].present?
      fields[:bio] = params[:bio] if params[:bio].present?
      fields[:theme] = params[:theme] if params[:theme].present?
      fields[:ui_scale] = params[:ui_scale] if params[:ui_scale].present?
      fields[:language] = params[:language] if params[:language].present?
      fields[:timezone] = params[:timezone] if params[:timezone].present?
      raise '更新するフィールドがありません' if fields.empty?
      user.update!(fields.merge(updated_at: Time.current))
    end
  end
end
