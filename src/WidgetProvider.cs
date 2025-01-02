using Microsoft.AdaptiveCards;
using Microsoft.UI.Xaml.Controls;
using System.IO;

namespace NetworkWidget
{
    public class WidgetProvider
    {
        private readonly string AdaptiveCardFile = "AdaptiveCard.json";

        public void InitializeWidget()
        {
            string cardJson = File.ReadAllText(AdaptiveCardFile);
            var adaptiveCard = AdaptiveCard.FromJson(cardJson);
            RenderAdaptiveCard(adaptiveCard);
        }

        private void RenderAdaptiveCard(AdaptiveCard card)
        {
            // Bind to WebView2 or UI rendering
            MainPage.AdaptiveCardView.NavigateToString(card.ToJson());
        }
    }
}
