class ImageService
  def initialize(user)
    @user = user
  end

  def save_whiteboard!(feature_id, board_id, image_data)
    raise '必要なパラメータが不足しています' if [feature_id, board_id, image_data].any?(&:blank?)
    header, encoded = image_data.split(',', 2)
    bytes = Base64.decode64(encoded)
    image_id = SecureRandom.uuid
    path = Rails.root.join('files', 'whiteboards', "#{image_id}.png")
    File.binwrite(path, bytes)
    FileRecord.create!(id: image_id, filename: "#{image_id}.png", original_filename: "whiteboard_#{board_id}.png", file_path: path.to_s, file_size: bytes.bytesize, mime_type: 'image/png', upload_by: @user.id, feature_id: feature_id)
    { success: true, data: { imageId: image_id, imagePath: path.to_s } }
  end
end
