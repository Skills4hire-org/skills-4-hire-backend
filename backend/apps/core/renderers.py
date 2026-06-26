from rest_framework.renderers import JSONRenderer


class StandardizedJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        # Keep DRF-generated errors intact to avoid double-wrapping
        if response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and data.get("success") is True:
            return super().render(data, accepted_media_type, renderer_context)

        message = "Operation successful"
        if isinstance(data, dict):
            message = data.pop("message", message)

        standardized = {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        }
        return super().render(standardized, accepted_media_type, renderer_context)
