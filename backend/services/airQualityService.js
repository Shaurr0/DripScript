/**
 * Air Quality Service - Integrates with AQICN and OpenWeather Air Pollution APIs
 * Handles air quality index and pollution data
 */

class AirQualityService {
  constructor(aqicnToken, openWeatherApiKey) {
    this.aqicnToken = aqicnToken;
    this.openWeatherApiKey = openWeatherApiKey;
    this.aqicnBaseUrl = 'https://api.waqi.info';
    this.openWeatherBaseUrl = 'https://api.openweathermap.org/data/2.5';
  }

  /**
   * Get air quality data using AQICN API
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Air quality data
   */
  async getAQIFromAQICN(lat, lon) {
    try {
      const response = await fetch(
        `${this.aqicnBaseUrl}/feed/geo:${lat};${lon}/?token=${this.aqicnToken}`
      );
      
      if (!response.ok) {
        throw new Error(`AQICN API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status !== 'ok') {
        throw new Error(`AQICN API returned status: ${data.status}`);
      }
      
      return {
        aqi: data.data.aqi,
        dominentPollutant: data.data.dominentpol,
        station: data.data.city.name,
        timestamp: data.data.time.s,
        attribution: data.data.attributions,
        pollutants: {
          pm25: data.data.iaqi?.pm25?.v || null,
          pm10: data.data.iaqi?.pm10?.v || null,
          o3: data.data.iaqi?.o3?.v || null,
          no2: data.data.iaqi?.no2?.v || null,
          so2: data.data.iaqi?.so2?.v || null,
          co: data.data.iaqi?.co?.v || null
        }
      };
    } catch (error) {
      console.error('Error fetching AQICN data:', error);
      throw error;
    }
  }

  /**
   * Get air pollution data using OpenWeather API
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Air pollution data
   */
  async getAirPollutionFromOpenWeather(lat, lon) {
    try {
      const response = await fetch(
        `${this.openWeatherBaseUrl}/air_pollution?lat=${lat}&lon=${lon}&appid=${this.openWeatherApiKey}`
      );
      
      if (!response.ok) {
        throw new Error(`OpenWeather Air Pollution API error: ${response.status}`);
      }
      
      const data = await response.json();
      const current = data.list[0];
      
      return {
        aqi: current.main.aqi,
        timestamp: new Date(current.dt * 1000).toISOString(),
        components: {
          co: current.components.co,
          no: current.components.no,
          no2: current.components.no2,
          o3: current.components.o3,
          so2: current.components.so2,
          pm2_5: current.components.pm2_5,
          pm10: current.components.pm10,
          nh3: current.components.nh3
        }
      };
    } catch (error) {
      console.error('Error fetching OpenWeather air pollution data:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive air quality data (tries AQICN first, fallback to OpenWeather)
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Comprehensive air quality data
   */
  async getAirQualityData(lat, lon) {
    try {
      // Try AQICN first (more detailed data)
      const aqicnData = await this.getAQIFromAQICN(lat, lon);
      return {
        source: 'AQICN',
        aqi: aqicnData.aqi,
        level: this.getAQILevel(aqicnData.aqi),
        description: this.getAQIDescription(aqicnData.aqi),
        dominentPollutant: aqicnData.dominentPollutant,
        station: aqicnData.station,
        timestamp: aqicnData.timestamp,
        pollutants: aqicnData.pollutants,
        healthRecommendation: this.getHealthRecommendation(aqicnData.aqi),
        clothingImpact: this.getClothingImpact(aqicnData.aqi)
      };
    } catch (aqicnError) {
      console.warn('AQICN failed, trying OpenWeather:', aqicnError.message);
      
      try {
        // Fallback to OpenWeather
        const owData = await this.getAirPollutionFromOpenWeather(lat, lon);
        // Convert OpenWeather AQI (1-5) to standard AQI scale
        const standardAQI = this.convertOpenWeatherAQI(owData.aqi);
        
        return {
          source: 'OpenWeather',
          aqi: standardAQI,
          level: this.getAQILevel(standardAQI),
          description: this.getAQIDescription(standardAQI),
          dominentPollutant: this.getDominentPollutant(owData.components),
          timestamp: owData.timestamp,
          components: owData.components,
          healthRecommendation: this.getHealthRecommendation(standardAQI),
          clothingImpact: this.getClothingImpact(standardAQI)
        };
      } catch (owError) {
        console.error('Both air quality APIs failed:', owError.message);
        // Return default/unknown data
        return {
          source: 'default',
          aqi: null,
          level: 'unknown',
          description: 'Air quality data unavailable',
          error: 'Unable to fetch air quality data'
        };
      }
    }
  }

  /**
   * Convert OpenWeather AQI scale (1-5) to standard AQI scale
   * @param {number} owAqi - OpenWeather AQI value
   * @returns {number} Standard AQI value
   */
  convertOpenWeatherAQI(owAqi) {
    const conversion = {
      1: 25,   // Good (0-50)
      2: 75,   // Fair (51-100)
      3: 125,  // Moderate (101-150)
      4: 175,  // Poor (151-200)
      5: 225   // Very Poor (201-300)
    };
    return conversion[owAqi] || 100;
  }

  /**
   * Get the dominant pollutant from components
   * @param {Object} components - Air pollution components
   * @returns {string} Dominant pollutant
   */
  getDominentPollutant(components) {
    let maxValue = 0;
    let dominant = 'pm2_5'; // default
    
    Object.entries(components).forEach(([key, value]) => {
      if (value > maxValue) {
        maxValue = value;
        dominant = key;
      }
    });
    
    return dominant;
  }

  /**
   * Get AQI level category
   * @param {number} aqi - Air Quality Index value
   * @returns {string} AQI level
   */
  getAQILevel(aqi) {
    if (aqi <= 50) return 'good';
    if (aqi <= 100) return 'moderate';
    if (aqi <= 150) return 'unhealthy_sensitive';
    if (aqi <= 200) return 'unhealthy';
    if (aqi <= 300) return 'very_unhealthy';
    return 'hazardous';
  }

  /**
   * Get AQI description
   * @param {number} aqi - Air Quality Index value
   * @returns {string} AQI description
   */
  getAQIDescription(aqi) {
    if (aqi <= 50) return 'Good - Air quality is satisfactory';
    if (aqi <= 100) return 'Moderate - Air quality is acceptable';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy - Everyone may experience health effects';
    if (aqi <= 300) return 'Very Unhealthy - Health alert';
    return 'Hazardous - Emergency conditions';
  }

  /**
   * Get health recommendations based on AQI
   * @param {number} aqi - Air Quality Index value
   * @returns {Object} Health recommendations
   */
  getHealthRecommendation(aqi) {
    if (aqi <= 50) {
      return {
        general: 'Great day for outdoor activities',
        sensitive: 'No restrictions'
      };
    } else if (aqi <= 100) {
      return {
        general: 'Outdoor activities are okay',
        sensitive: 'Consider reducing prolonged outdoor exertion'
      };
    } else if (aqi <= 150) {
      return {
        general: 'Reduce prolonged outdoor exertion',
        sensitive: 'Avoid outdoor activities'
      };
    } else if (aqi <= 200) {
      return {
        general: 'Avoid outdoor activities',
        sensitive: 'Stay indoors'
      };
    } else {
      return {
        general: 'Stay indoors, use air purifiers',
        sensitive: 'Avoid all outdoor activities'
      };
    }
  }

  /**
   * Get clothing recommendations based on air quality
   * @param {number} aqi - Air Quality Index value
   * @returns {Object} Clothing impact recommendations
   */
  getClothingImpact(aqi) {
    if (aqi <= 50) {
      return {
        mask: false,
        coverage: 'normal',
        recommendation: 'No special clothing needed'
      };
    } else if (aqi <= 100) {
      return {
        mask: false,
        coverage: 'normal',
        recommendation: 'Light layers recommended'
      };
    } else if (aqi <= 150) {
      return {
        mask: true,
        coverage: 'more',
        recommendation: 'Wear mask, cover exposed skin'
      };
    } else {
      return {
        mask: true,
        coverage: 'full',
        recommendation: 'Wear N95 mask, minimize skin exposure'
      };
    }
  }
}

export default AirQualityService;