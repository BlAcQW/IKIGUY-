"""
Property Context Service for EstateFlow.

Converts property data into AI-optimized context strings for chat interactions.
Implements context caching to reduce token costs.
"""

from typing import Optional
from app.models.property import Property


class PropertyContextService:
    """Service for building AI-optimized context from property data."""

    @staticmethod
    def build_property_context(property_data: Property, language: str = "en") -> str:
        """
        Build rich context string from property data.

        Prioritizes frequently-asked information and formats for LLM readability.

        Args:
            property_data: Property model instance
            language: Language code (en, es, fr)

        Returns:
            Formatted context string optimized for LLM processing
        """
        # Format price with currency symbol
        price_usd = property_data.financial.price_usd
        price_formatted = f"${price_usd:,.0f}"

        # Build context sections
        context_parts = []

        # Header with basic info
        context_parts.append(f"# Property: {property_data.name}")
        context_parts.append(f"Type: {property_data.property_type}")
        context_parts.append(f"Status: {property_data.status}")
        context_parts.append(f"Description: {property_data.description}\n")

        # Location
        context_parts.append("## Location")
        location = property_data.location
        context_parts.append(f"Address: {location.address}")
        context_parts.append(f"City: {location.city}, {location.state}")
        context_parts.append(f"Country: {location.country}")
        if location.neighborhood:
            context_parts.append(f"Neighborhood: {location.neighborhood}\n")

        # Property Features
        context_parts.append("## Property Features")
        features = property_data.features
        context_parts.append(f"- {features.bedrooms} bedrooms, {features.bathrooms} bathrooms")
        context_parts.append(f"- {features.sqft:,.0f} square feet")
        if features.lot_size:
            context_parts.append(f"- Lot size: {features.lot_size:,.0f} sq ft")
        if features.year_built:
            context_parts.append(f"- Built in {features.year_built}")
        if features.parking_spaces:
            context_parts.append(f"- {features.parking_spaces} parking spaces")

        # Amenities
        amenities = []
        if features.pool:
            amenities.append("pool")
        if features.garden:
            amenities.append("garden")
        if features.balcony:
            amenities.append("balcony")
        if features.elevator:
            amenities.append("elevator")
        if features.air_conditioning:
            amenities.append("air conditioning")
        if features.heating:
            amenities.append("heating")
        if features.security_system:
            amenities.append("security system")
        if features.gym:
            amenities.append("gym")

        if amenities:
            context_parts.append(f"- Amenities: {', '.join(amenities)}")

        if features.furnished is not None:
            furnished_status = "Furnished" if features.furnished else "Unfurnished"
            context_parts.append(f"- {furnished_status}\n")

        # Pet Policy - Important for common questions
        context_parts.append("## Pet Policy")
        pet_policy = features.pet_policy
        if pet_policy == "allowed":
            context_parts.append("Pets are allowed.")
        elif pet_policy == "not_allowed":
            context_parts.append("Pets are not allowed.")
        elif pet_policy == "allowed_with_deposit":
            deposit = features.pet_deposit or 500  # Default if not specified
            context_parts.append(f"Pets are allowed with approval and a ${deposit:,.0f} deposit.")
        else:
            context_parts.append("Pet policy: Contact agent for details.\n")

        # Pricing and Costs
        context_parts.append("\n## Pricing")
        context_parts.append(f"- Price: {price_formatted}")
        financial = property_data.financial
        if financial.hoa_fees_monthly:
            context_parts.append(f"- HOA fees: ${financial.hoa_fees_monthly:,.0f}/month")
        if financial.property_tax_annual:
            context_parts.append(f"- Property tax: ${financial.property_tax_annual:,.0f}/year")
        if financial.insurance_estimate:
            context_parts.append(f"- Insurance estimate: ${financial.insurance_estimate:,.0f}/year\n")

        # Neighborhood Data
        neighborhood = property_data.neighborhood_data
        if neighborhood:
            context_parts.append("## Neighborhood")
            if neighborhood.safety_rating:
                context_parts.append(f"- Safety rating: {neighborhood.safety_rating}/10")
            if neighborhood.walkability_score:
                context_parts.append(f"- Walkability score: {neighborhood.walkability_score}/100")
            if neighborhood.transit_score:
                context_parts.append(f"- Transit score: {neighborhood.transit_score}/100")

            # Schools
            if neighborhood.schools:
                context_parts.append("\n### Nearby Schools")
                for i, school in enumerate(neighborhood.schools[:5], 1):  # Limit to 5
                    school_info = f"- {school.name}"
                    if school.type:
                        school_info += f" ({school.type})"
                    if school.distance_km:
                        school_info += f": {school.distance_km:.1f}km away"
                    if school.rating:
                        school_info += f" (rated {school.rating}/10)"
                    context_parts.append(school_info)

            # Amenities
            if neighborhood.amenities:
                context_parts.append("\n### Nearby Amenities")
                # Group amenities by category
                amenities_by_category = {}
                for amenity in neighborhood.amenities[:10]:  # Limit to 10
                    category = amenity.category or "Other"
                    if category not in amenities_by_category:
                        amenities_by_category[category] = []
                    amenity_info = amenity.name
                    if amenity.distance_km:
                        amenity_info += f" ({amenity.distance_km:.1f}km)"
                    amenities_by_category[category].append(amenity_info)

                for category, items in amenities_by_category.items():
                    context_parts.append(f"- {category}: {', '.join(items)}")

        # Agent Information
        if property_data.agent_name:
            context_parts.append(f"\n## Contact")
            context_parts.append(f"Agent: {property_data.agent_name}")
            context_parts.append("For viewings and detailed inquiries, please contact the agent.")

        return "\n".join(context_parts)

    @staticmethod
    def get_mortgage_estimate(
        price: float,
        down_payment_percent: float = 20.0,
        interest_rate: float = 7.0,
        years: int = 30
    ) -> dict:
        """
        Calculate mortgage estimate.

        Args:
            price: Property price in USD
            down_payment_percent: Down payment as percentage (default 20%)
            interest_rate: Annual interest rate as percentage (default 7%)
            years: Loan term in years (default 30)

        Returns:
            Dictionary with mortgage details
        """
        down_payment = price * (down_payment_percent / 100)
        loan_amount = price - down_payment
        monthly_rate = (interest_rate / 100) / 12
        num_payments = years * 12

        # Monthly payment formula: M = P[r(1+r)^n]/[(1+r)^n-1]
        if monthly_rate > 0:
            monthly_payment = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** num_payments
            ) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_payment = loan_amount / num_payments

        return {
            "price": price,
            "down_payment": down_payment,
            "down_payment_percent": down_payment_percent,
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "years": years,
            "monthly_payment": monthly_payment,
            "total_paid": monthly_payment * num_payments,
            "total_interest": (monthly_payment * num_payments) - loan_amount
        }

    @staticmethod
    def format_mortgage_response(mortgage_data: dict, language: str = "en") -> str:
        """
        Format mortgage calculation for user-friendly response.

        Args:
            mortgage_data: Mortgage calculation from get_mortgage_estimate
            language: Language code (en, es, fr)

        Returns:
            Formatted mortgage information string
        """
        if language == "en":
            return (
                f"Based on standard assumptions ({mortgage_data['down_payment_percent']:.0f}% down, "
                f"{mortgage_data['interest_rate']:.1f}% interest, {mortgage_data['years']} years):\n"
                f"- Down payment: ${mortgage_data['down_payment']:,.0f}\n"
                f"- Loan amount: ${mortgage_data['loan_amount']:,.0f}\n"
                f"- Monthly payment: ${mortgage_data['monthly_payment']:,.0f}\n"
                f"- Total paid over {mortgage_data['years']} years: ${mortgage_data['total_paid']:,.0f}\n\n"
                f"Note: This is an estimate. Actual rates may vary. Consult a mortgage advisor for precise calculations."
            )
        elif language == "es":
            return (
                f"Basado en suposiciones estándar ({mortgage_data['down_payment_percent']:.0f}% de enganche, "
                f"{mortgage_data['interest_rate']:.1f}% de interés, {mortgage_data['years']} años):\n"
                f"- Enganche: ${mortgage_data['down_payment']:,.0f}\n"
                f"- Monto del préstamo: ${mortgage_data['loan_amount']:,.0f}\n"
                f"- Pago mensual: ${mortgage_data['monthly_payment']:,.0f}\n"
                f"- Total pagado en {mortgage_data['years']} años: ${mortgage_data['total_paid']:,.0f}\n\n"
                f"Nota: Esta es una estimación. Las tasas reales pueden variar. Consulte a un asesor hipotecario."
            )
        elif language == "fr":
            return (
                f"Basé sur des hypothèses standard ({mortgage_data['down_payment_percent']:.0f}% d'acompte, "
                f"{mortgage_data['interest_rate']:.1f}% d'intérêt, {mortgage_data['years']} ans):\n"
                f"- Acompte: ${mortgage_data['down_payment']:,.0f}\n"
                f"- Montant du prêt: ${mortgage_data['loan_amount']:,.0f}\n"
                f"- Paiement mensuel: ${mortgage_data['monthly_payment']:,.0f}\n"
                f"- Total payé sur {mortgage_data['years']} ans: ${mortgage_data['total_paid']:,.0f}\n\n"
                f"Note: Ceci est une estimation. Les taux réels peuvent varier. Consultez un conseiller hypothécaire."
            )
        else:
            return format_mortgage_response(mortgage_data, "en")
