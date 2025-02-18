import React, { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import config, { log } from '../config';
import {
  Container,
  IframeContainer,
  StyledIframe,
  SelectorInfo,
  SelectorCode,
  Loading,
  ErrorMessage,
  MatchesList,
  MatchItem,
  MatchText,
  AttributesContainer,
  Attribute,
  Suggestions,
  PatternAnalysis,
} from './ElementSelector.styles';

// CRITICAL: This component handles the core selector functionality
// TODO(future): Add pattern recognition UI
// CHECK(periodic): Verify selector accuracy

interface ElementSelectorProps {
  configId: string;
  url: string;
  onSelectorChange: (selector: string) => void;
}

interface SelectorSuggestion {
  selector: string;
  type: 'basic' | 'unique' | 'pattern';
  description: string;
}

interface MatchedElement {
  tag: string;
  text: string;
  attributes: Record<string, string>;
  suggested_selectors: SelectorSuggestion[];
}

interface PatternAnalysis {
  page_structure: {
    elements: Record<string, number>;
    patterns: Record<string, string[]>;
    recommendations: Array<{
      element_type: string;
      suggested_selectors: string[];
      confidence: number;
    }>;
  };
  similar_elements: number;
  confidence: number;
}

export const ElementSelector: React.FC<ElementSelectorProps> = ({
  configId,
  url,
  onSelectorChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<MatchedElement[]>([]);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [currentSelector, setCurrentSelector] = useState<string>('');

  // WebSocket connection for real-time selector testing
  const { sendMessage, lastMessage, readyState, reconnect } = useWebSocket(
    `${config.api.wsUrl}/ws/crawling/selector/${configId}/`
  );

  interface WebSocketResponse {
    type: 'selector_results' | 'error' | 'page_analysis';
    selector?: string;
    matches?: MatchedElement[];
    count?: number;
    message?: string;
    pattern_analysis?: PatternAnalysis;
  }

  const [wsData, setWsData] = useState<WebSocketResponse | null>(null);

  useEffect(() => {
    if (lastMessage) {
      try {
        const data: WebSocketResponse = JSON.parse(lastMessage);
        log.debug('WebSocket message received:', data);
        
        if (data.type === 'selector_results') {
          setMatches(data.matches || []);
          setWsData(data);
          setLoading(false);
        } else if (data.type === 'error') {
          log.error('Selector test error:', data.message);
          setError(data.message || 'Unknown error');
          setLoading(false);
        }
      } catch (e) {
        log.error('Failed to parse WebSocket message:', e);
        setError('Failed to parse WebSocket message');
        setLoading(false);
      }
    }
  }, [lastMessage]);

  // Initialize iframe content with selection script
  useEffect(() => {
    const iframe = iframeRef.current;
    if (iframe && iframe.contentWindow) {
      const script = `
        document.addEventListener('mouseover', function(e) {
          e.stopPropagation();
          const oldHighlight = document.querySelector('.selector-highlight');
          if (oldHighlight) {
            oldHighlight.classList.remove('selector-highlight');
          }
          e.target.classList.add('selector-highlight');
        }, true);

        document.addEventListener('mouseout', function(e) {
          e.target.classList.remove('selector-highlight');
        }, true);

        document.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          
          // Generate selector
          let element = e.target;
          let selector = '';
          
          // Try ID first
          if (element.id) {
            selector = '#' + element.id;
          } else {
            // Build selector from classes and attributes
            let classes = Array.from(element.classList)
              .filter(c => c !== 'selector-highlight')
              .join('.');
            selector = element.tagName.toLowerCase() +
              (classes ? '.' + classes : '');
              
            // Add unique attributes if needed
            if (element.getAttribute('data-testid')) {
              selector += '[data-testid="' + element.getAttribute('data-testid') + '"]';
            }
          }
          
          window.parent.postMessage({
            type: 'ELEMENT_SELECTED',
            selector: selector
          }, '*');
        }, true);

        // Add highlight styles
        const style = document.createElement('style');
        style.textContent = \`
          .selector-highlight {
            outline: 2px solid #007bff !important;
            outline-offset: 2px !important;
          }
        \`;
        document.head.appendChild(style);
      `;

      // Inject script after iframe loads
      iframe.onload = () => {
        const doc = iframe.contentDocument;
        if (doc) {
          const scriptEl = doc.createElement('script');
          scriptEl.textContent = script;
          doc.body.appendChild(scriptEl);
        }
      };
    }
  }, []);

  // Handle element selection message from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'ELEMENT_SELECTED') {
        const selector = event.data.selector;
        log.debug('Element selected:', selector);
        setCurrentSelector(selector);
        onSelectorChange(selector);
        
        // Test selector via WebSocket
        setLoading(true);
        sendMessage(JSON.stringify({
          action: 'test_selector',
          selector,
          url
        }));
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onSelectorChange, sendMessage, url]);

  return (
    <Container>
      <IframeContainer style={{ height: `${config.ui.maxIframeHeight}px` }}>
        <StyledIframe
          ref={iframeRef}
          src={url}
          title="Page Preview"
          sandbox="allow-same-origin allow-scripts"
        />
      </IframeContainer>

      {currentSelector && (
        <SelectorInfo>
          <h3>Current Selector:</h3>
          <SelectorCode>{currentSelector}</SelectorCode>
          
          {loading && <Loading>Testing selector...</Loading>}
          
          {error && (
            <ErrorMessage>
              Error: {error}
              <button onClick={reconnect}>Retry Connection</button>
            </ErrorMessage>
          )}
          
          {matches.length > 0 && (
            <>
              <MatchesList>
                <h4>Matching Elements ({matches.length}):</h4>
                <ul>
                  {matches.map((match, index) => (
                    <MatchItem key={index}>
                      <strong>{match.tag}</strong>
                      {match.text && <MatchText>: {match.text}</MatchText>}
                      <AttributesContainer>
                        {Object.entries(match.attributes).map(([key, value]) => (
                          <Attribute key={key}>
                            {key}="{value}"
                          </Attribute>
                        ))}
                      </AttributesContainer>
                      {match.suggested_selectors && match.suggested_selectors.length > 0 && (
                        <Suggestions>
                          <h5>Suggested Selectors:</h5>
                          <ul>
                            {match.suggested_selectors.map((suggestion, idx) => (
                              <li key={idx} onClick={() => onSelectorChange(suggestion.selector)}>
                                <code>{suggestion.selector}</code>
                                <span className="type">{suggestion.type}</span>
                                <span className="description">{suggestion.description}</span>
                              </li>
                            ))}
                          </ul>
                        </Suggestions>
                      )}
                    </MatchItem>
                  ))}
                </ul>
              </MatchesList>

              {wsData?.pattern_analysis && (
                <PatternAnalysis>
                  <h4>Pattern Analysis</h4>
                  <div className="stats">
                    <div>
                      <strong>Similar Elements:</strong> {wsData.pattern_analysis.similar_elements}
                    </div>
                    <div>
                      <strong>Confidence:</strong>{' '}
                      {(wsData.pattern_analysis.confidence * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div className="recommendations">
                    <h5>Recommended Patterns:</h5>
                    <ul>
                      {wsData.pattern_analysis.page_structure.recommendations.map((rec: {
                        element_type: string;
                        suggested_selectors: string[];
                        confidence: number;
                      }, idx: number) => (
                        <li key={idx}>
                          <div className="element-type">{rec.element_type}</div>
                          <div className="selectors">
                            {rec.suggested_selectors.map((selector: string, sIdx: number) => (
                              <code
                                key={sIdx}
                                onClick={() => onSelectorChange(selector)}
                                className="clickable"
                              >
                                {selector}
                              </code>
                            ))}
                          </div>
                          <div className="confidence">
                            Confidence: {(rec.confidence * 100).toFixed(1)}%
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </PatternAnalysis>
              )}
            </>
          )}
        </SelectorInfo>
      )}
    </Container>
  );
};

export default ElementSelector;
