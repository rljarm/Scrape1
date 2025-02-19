# Configuration settings for the application

class Config:
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

# Can add more configurations like ProductionConfig if needed

# Active configuration
config = DevelopmentConfig()
